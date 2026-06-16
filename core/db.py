"""
数据库存储层 — SQLite + SpatiaLite 替代 CSV 文件存储

使用方式:
    from core.db import EmotionDB
    db = EmotionDB()
    db.insert_points(df)                    # 写入点数据
    points = db.query_by_bbox(111, 30, 112, 31)  # 空间范围查询
    stats = db.get_polarity_stats()          # 极性统计
    db.export_csv("/path/to/output.csv")     # 导出 CSV
"""
import os
import sys
import sqlite3
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import PROCESSED_DIR

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(PROCESSED_DIR), 'emotion_map.db')


class EmotionDB:
    """情绪地图 SQLite 数据库管理器。

    三张核心表:
      - points: 情绪数据点（含坐标、分数、极性、文本等）
      - boundaries: 分析范围边界
      - analysis_runs: 分析运行记录
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    # ── 表管理 ──

    def init_schema(self):
        """初始化数据库表结构（幂等）。"""
        self.conn.executescript("""
        CREATE TABLE IF NOT EXISTS points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lon REAL NOT NULL,
            lat REAL NOT NULL,
            score REAL DEFAULT 0.5,
            polarity TEXT DEFAULT 'Neutral',
            keywords TEXT DEFAULT '',
            text TEXT DEFAULT '',
            source TEXT DEFAULT '',
            source_url TEXT DEFAULT '',
            category TEXT DEFAULT '',
            intensity REAL,
            target_type TEXT DEFAULT '',
            target_detail TEXT DEFAULT '',
            confidence_l2 REAL,
            confidence_l3 REAL,
            confidence_l4 REAL,
            attributions TEXT DEFAULT '',
            suggestions TEXT DEFAULT '',
            level TEXT DEFAULT 'L2',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_points_polarity ON points(polarity);
        CREATE INDEX IF NOT EXISTS idx_points_score ON points(score);
        CREATE INDEX IF NOT EXISTS idx_points_lon_lat ON points(lon, lat);
        CREATE INDEX IF NOT EXISTS idx_points_level ON points(level);
        CREATE INDEX IF NOT EXISTS idx_points_source ON points(source);

        CREATE TABLE IF NOT EXISTS boundaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            geojson TEXT NOT NULL,
            style TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS analysis_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            input_file TEXT,
            output_file TEXT,
            engine_type TEXT,
            n_input INTEGER,
            n_output INTEGER,
            duration_sec REAL,
            polarity_stats TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self.conn.commit()

    def drop_all(self):
        """删除所有表（仅测试用）。"""
        self.conn.executescript("""
        DROP TABLE IF EXISTS points;
        DROP TABLE IF EXISTS boundaries;
        DROP TABLE IF EXISTS analysis_runs;
        """)
        self.conn.commit()

    # ── 点数据操作 ──

    def insert_points(self, df: pd.DataFrame, level: str = 'L2',
                      batch_size: int = 5000):
        """从 DataFrame 批量插入点数据。

        Args:
            df: 含 lon/lat/score/polarity 等字段的 DataFrame
            level: 数据层级 L1/L2/L3/L4
            batch_size: 每批插入行数
        """
        # 列名映射（DataFrame → points 表）
        col_map = {
            'lon': 'lon', 'lat': 'lat', 'score': 'score',
            'polarity': 'polarity', 'keywords': 'keywords',
            'text': 'text', 'comments': 'text',
            'source': 'source', 'source_url': 'source_url',
            'category': 'category', 'intensity': 'intensity',
            'target_type': 'target_type', 'target_detail': 'target_detail',
            'l2_confidence': 'confidence_l2',
            'l3_confidence': 'confidence_l3',
            'l4_confidence': 'confidence_l4',
            'attributions': 'attributions', 'suggestions': 'suggestions',
        }

        # 构建插入行
        rows = []
        required_cols = {'lon', 'lat'}
        for _, row in df.iterrows():
            record = {'level': level}
            for df_col, db_col in col_map.items():
                if df_col in df.columns:
                    val = row[df_col]
                    if isinstance(val, float) and np.isnan(val):
                        continue
                    record[db_col] = val
            # 必须有坐标
            if not all(c in record for c in required_cols):
                continue
            rows.append(record)

        # 批量插入
        if not rows:
            return 0

        columns = list(rows[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        col_names = ', '.join(columns)
        sql = f"INSERT INTO points ({col_names}) VALUES ({placeholders})"

        total = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            self.conn.executemany(sql, [
                tuple(r.get(c, None) for c in columns)
                for r in batch
            ])
            total += len(batch)
        self.conn.commit()
        return total

    def query_by_bbox(self, min_lon: float, min_lat: float,
                      max_lon: float, max_lat: float,
                      level: str = None) -> pd.DataFrame:
        """按空间范围查询点数据。"""
        sql = """
        SELECT * FROM points
        WHERE lon BETWEEN ? AND ?
          AND lat BETWEEN ? AND ?
        """
        params = [min_lon, max_lon, min_lat, max_lat]

        if level:
            sql += " AND level = ?"
            params.append(level)

        df = pd.read_sql_query(sql, self.conn, params=params)
        return df

    def get_polarity_stats(self, level: str = None) -> dict:
        """获取五级极性统计。"""
        sql = """
        SELECT polarity, COUNT(*) as cnt
        FROM points
        """
        params = []
        if level:
            sql += " WHERE level = ?"
            params.append(level)
        sql += " GROUP BY polarity"

        df = pd.read_sql_query(sql, self.conn, params=params)
        stats = {
            'Very Positive': 0, 'Positive': 0, 'Neutral': 0,
            'Negative': 0, 'Very Negative': 0,
        }
        for _, row in df.iterrows():
            if row['polarity'] in stats:
                stats[row['polarity']] = int(row['cnt'])
        stats['total'] = sum(stats.values())
        return stats

    def get_score_distribution(self, bins: int = 10) -> pd.DataFrame:
        """获取分数分布直方图数据。"""
        sql = """
        SELECT
            CAST(score * ? AS INTEGER) as score_bin,
            COUNT(*) as cnt
        FROM points
        GROUP BY score_bin
        ORDER BY score_bin
        """
        return pd.read_sql_query(sql, self.conn, params=[bins])

    def count(self, level: str = None) -> int:
        """获取点总数。"""
        if level:
            row = self.conn.execute(
                "SELECT COUNT(*) as n FROM points WHERE level = ?",
                [level]
            ).fetchone()
        else:
            row = self.conn.execute(
                "SELECT COUNT(*) as n FROM points"
            ).fetchone()
        return row['n'] if row else 0

    def export_csv(self, output_path: str, level: str = None):
        """导出为 CSV 文件。"""
        if level:
            df = pd.read_sql_query(
                "SELECT * FROM points WHERE level = ?",
                self.conn, params=[level]
            )
        else:
            df = pd.read_sql_query("SELECT * FROM points", self.conn)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        return len(df)

    # ── 从 CSV 导入 ──

    def import_csv(self, csv_path: str, level: str = None) -> int:
        """从 CSV/GeoJSON 文件导入数据到数据库。

        Args:
            csv_path: 文件路径
            level: 数据层级（自动检测或手动指定）
        Returns:
            导入行数
        """
        from core.data_loader import load_emotion_data

        data = load_emotion_data(csv_path)
        if not data:
            return 0

        df = data['df']
        if level is None:
            # 自动检测层级
            fname = os.path.basename(csv_path)
            if '_L4_' in fname or 'L4_result' in fname:
                level = 'L4'
            elif '_L3_' in fname or 'L3_result' in fname:
                level = 'L3'
            elif '_L2_' in fname or 'L2_result' in fname:
                level = 'L2'
            else:
                level = 'L1'

        return self.insert_points(df, level=level)

    def close(self):
        """关闭数据库连接。"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        self.init_schema()
        return self

    def __exit__(self, *args):
        self.close()
