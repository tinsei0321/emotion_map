# ══════════════════════════════════════════════════════════════
# Design Tokens — Auto-generated from design/tokens.json
# DO NOT EDIT MANUALLY — Run: python design/generate_css.py
# ══════════════════════════════════════════════════════════════
#
# 支持 Light/Dark 双主题:
#   from design.tokens import DARK_TOKENS, LIGHT_TOKENS, get_token
#   primary = get_token('color-brand-primary', theme='dark')
#
# 向后兼容（默认 dark 主题常量）:
#   from design.tokens import COLOR_BRAND_PRIMARY, RADIUS_MD
#



# ════════════════════════════════════════════════════════
#  基础 Token（与主题无关）
# ════════════════════════════════════════════════════════

# ── effect ──
EFFECT_BACKDROP_BLUR_LG = '12px'
EFFECT_BACKDROP_BLUR_MD = '8px'
EFFECT_BACKDROP_BLUR_SM = '4px'
EFFECT_OPACITY_BOUNDARY_FILL = 0.08
EFFECT_OPACITY_DISABLED = 0.4
EFFECT_OPACITY_FILL_HIGH = 0.92
EFFECT_OPACITY_FILL_LOW = 0.12
EFFECT_OPACITY_HOVER = 0.8
EFFECT_OPACITY_OVERLAY = 0.55
EFFECT_TRANSITION_FAST = '0.15s ease'
EFFECT_TRANSITION_NORMAL = '0.2s ease'
EFFECT_TRANSITION_SLOW = '0.3s ease'

# ── geojson ──
GEOJSON__DOC = 'geojson.io 1:1 设计语言 (source: docs/vision-inbox/latest.md). Light-first. 前端唯一 token 源, 经 generate_css.py 生成 frontend/css/tokens.css. emotion 五色保留语义, 其余对齐 geojson.io.'
GEOJSON_COLOR_BORDER_DEFAULT = '#e5e5e5'
GEOJSON_COLOR_BORDER_STRONG = '#d4d4d4'
GEOJSON_COLOR_BRAND_ACTIVE = '#004691'
GEOJSON_COLOR_BRAND_FOCUS = '#3195ff'
GEOJSON_COLOR_BRAND_HOVER = '#0060c7'
GEOJSON_COLOR_BRAND_PRIMARY = '#007afc'
GEOJSON_COLOR_BRAND_SELECTED = '#007afc'
GEOJSON_COLOR_CHROME_ACTIVE_FILL = '#007afc'
GEOJSON_COLOR_CHROME_BORDER_BOTTOM = '#e5e5e5'
GEOJSON_COLOR_CHROME_DIVIDER = '#e5e5e5'
GEOJSON_COLOR_CHROME_HOVER_OVERLAY = '#f5f5f5'
GEOJSON_COLOR_CHROME_TEXT = '#404040'
GEOJSON_COLOR_CHROME_TITLE_BAR_BG = '#0c1c2e'
GEOJSON_COLOR_CHROME_TOOLBAR_BG = '#ffffff'
GEOJSON_COLOR_DANGER = '#dc2626'
GEOJSON_COLOR_EMOTION_NEGATIVE = '#C4956A'
GEOJSON_COLOR_EMOTION_NEUTRAL = '#C0C0C0'
GEOJSON_COLOR_EMOTION_POSITIVE = '#5DADE2'
GEOJSON_COLOR_EMOTION_VERY_NEGATIVE = '#B92D2D'
GEOJSON_COLOR_EMOTION_VERY_POSITIVE = '#78DC32'
GEOJSON_COLOR_GRAY_100 = '#f5f5f5'
GEOJSON_COLOR_GRAY_200 = '#e5e5e5'
GEOJSON_COLOR_GRAY_300 = '#d4d4d4'
GEOJSON_COLOR_GRAY_400 = '#a3a3a3'
GEOJSON_COLOR_GRAY_50 = '#fafafa'
GEOJSON_COLOR_GRAY_500 = '#737373'
GEOJSON_COLOR_GRAY_600 = '#525252'
GEOJSON_COLOR_GRAY_700 = '#404040'
GEOJSON_COLOR_GRAY_800 = '#262626'
GEOJSON_COLOR_GRAY_900 = '#171717'
GEOJSON_COLOR_IMPORT_PANEL_BORDER = '#E0E0E0'
GEOJSON_COLOR_IMPORT_PANEL_BUTTON_BORDER = '#CBD5E0'
GEOJSON_COLOR_IMPORT_PANEL_BUTTON_HOVER_BG = '#F7FAFC'
GEOJSON_COLOR_IMPORT_PANEL_PRIMARY_TEXT = '#2D3748'
GEOJSON_COLOR_IMPORT_PANEL_SECONDARY_TEXT = '#4A5568'
GEOJSON_COLOR_IMPORT_PANEL_TERTIARY_TEXT = '#718096'
GEOJSON_COLOR_OVERLAY = 'rgba(0,0,0,0.2)'
GEOJSON_COLOR_PILL_BG = 'rgba(0,122,252,0.10)'
GEOJSON_COLOR_PILL_FG = '#007afc'
GEOJSON_COLOR_SECTION_BODY_BG = '#ffffff'
GEOJSON_COLOR_SECTION_CHEVRON = '#737373'
GEOJSON_COLOR_SECTION_HEADER_BG = '#f5f5f5'
GEOJSON_COLOR_SECTION_HEADER_BORDER = '#e5e5e5'
GEOJSON_COLOR_SECTION_TAB_ACTIVE_BG = '#ffffff'
GEOJSON_COLOR_SECTION_TAB_BORDER = '#e5e5e5'
GEOJSON_COLOR_SECTION_TAB_INACTIVE_BG = '#ffffff'
GEOJSON_COLOR_SURFACE_MAP_BG = '#f5f5f5'
GEOJSON_COLOR_SURFACE_PAGE = '#ffffff'
GEOJSON_COLOR_SURFACE_PANEL = '#ffffff'
GEOJSON_COLOR_SURFACE_PANEL_ALT = '#f8f8f8'
GEOJSON_COLOR_TABLE_BORDER = '#e5e5e5'
GEOJSON_COLOR_TABLE_CELL_BG = '#ffffff'
GEOJSON_COLOR_TABLE_CELL_TEXT = '#171717'
GEOJSON_COLOR_TABLE_HEADER_BG = '#f5f5f5'
GEOJSON_COLOR_TABLE_HEADER_TEXT = '#171717'
GEOJSON_COLOR_TABLE_ROW_HOVER = '#f5f5f5'
GEOJSON_COLOR_TEXT_DISABLED = '#cfcfcf'
GEOJSON_COLOR_TEXT_INVERSE = '#ffffff'
GEOJSON_COLOR_TEXT_INVERSE_SOFT = 'rgba(255,255,255,0.7)'
GEOJSON_COLOR_TEXT_PRIMARY = '#404040'
GEOJSON_COLOR_TEXT_SECONDARY = '#737373'
GEOJSON_COLOR_TEXT_TERTIARY = '#a3a3a3'
GEOJSON_FEATURE_BOUNDARY_FILL = '#007afc'
GEOJSON_FEATURE_BOUNDARY_FILL_OPACITY = 0.08
GEOJSON_FEATURE_BOUNDARY_STROKE = '#007afc'
GEOJSON_FEATURE_BOUNDARY_STROKE_WIDTH = 1.5
GEOJSON_FEATURE_POINT_RADIUS = 5
GEOJSON_FEATURE_POINT_STROKE = '#ffffff'
GEOJSON_FEATURE_POINT_STROKE_WIDTH = 1
GEOJSON_FEATURE_SELECTION_HALO_COLOR = '#007afc'
GEOJSON_FEATURE_SELECTION_HALO_OPACITY = 0.25
GEOJSON_FEATURE_SELECTION_HALO_SCALE = 1.8
GEOJSON_FEATURE_VERTEX_COLOR = '#007afc'
GEOJSON_LAYOUT_COLLAPSE_BUTTON_SIZE = '40px'
GEOJSON_LAYOUT_HEADER_HEIGHT = '88px'
GEOJSON_LAYOUT_LEFT_PANEL_MAX = '1800px'
GEOJSON_LAYOUT_LEFT_PANEL_MIN = '220px'
GEOJSON_LAYOUT_LEFT_PANEL_WIDTH = '300px'
GEOJSON_LAYOUT_PANEL_WIDTH = '320px'
GEOJSON_LAYOUT_POPUP_WIDTH = '280px'
GEOJSON_LAYOUT_RIGHT_PANEL_MAX = '1800px'
GEOJSON_LAYOUT_RIGHT_PANEL_MIN = '240px'
GEOJSON_LAYOUT_RIGHT_PANEL_WIDTH = '340px'
GEOJSON_LAYOUT_SEARCH_COLLAPSED_SIZE = '32px'
GEOJSON_LAYOUT_SEARCH_WIDTH = '200px'
GEOJSON_LAYOUT_SEARCH_Z_INDEX = 96
GEOJSON_LAYOUT_SPLITTER_WIDTH = '8px'
GEOJSON_LAYOUT_TITLE_BAR_HEIGHT = '40px'
GEOJSON_LAYOUT_TOOLBAR_HEIGHT = '48px'
GEOJSON_RADIUS_FULL = '9999px'
GEOJSON_RADIUS_LG = '8px'
GEOJSON_RADIUS_MD = '6px'
GEOJSON_RADIUS_SM = '4px'
GEOJSON_RADIUS_XS = '2px'
GEOJSON_SHADOW_LG = '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)'
GEOJSON_SHADOW_MD = '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)'
GEOJSON_SHADOW_SM = '0 1px 2px 0 rgb(0 0 0 / 0.05)'
GEOJSON_SHADOW_TOOLBAR = '0 2px 10px 2px rgba(0,0,0,0.1)'
GEOJSON_SPACING_1 = '4px'
GEOJSON_SPACING_2 = '8px'
GEOJSON_SPACING_3 = '12px'
GEOJSON_SPACING_4 = '16px'
GEOJSON_SPACING_5 = '20px'
GEOJSON_SPACING_6 = '24px'
GEOJSON_SPACING_8 = '32px'
GEOJSON_TRANSITION = '150ms cubic-bezier(0.4, 0, 0.2, 1)'
GEOJSON_TYPOGRAPHY_LETTER_SPACING_NORMAL = 0
GEOJSON_TYPOGRAPHY_LETTER_SPACING_TIGHT = '-0.01em'
GEOJSON_TYPOGRAPHY_LETTER_SPACING_WIDE = '0.02em'
GEOJSON_TYPOGRAPHY_LETTER_SPACING_WIDER = '0.04em'
GEOJSON_TYPOGRAPHY_LINE_HEIGHT_NONE = 1
GEOJSON_TYPOGRAPHY_LINE_HEIGHT_NORMAL = 1.5
GEOJSON_TYPOGRAPHY_LINE_HEIGHT_RELAXED = 1.625
GEOJSON_TYPOGRAPHY_LINE_HEIGHT_TIGHT = 1.25
GEOJSON_TYPOGRAPHY_MONO = "'Source Code Pro', ui-monospace, 'Cascadia Code', Consolas, monospace"
GEOJSON_TYPOGRAPHY_SANS = "'Open Sans', 'Inter', system-ui, -apple-system, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif"
GEOJSON_TYPOGRAPHY_SIZE_2XL = '1.5rem'
GEOJSON_TYPOGRAPHY_SIZE_2XS = '0.625rem'
GEOJSON_TYPOGRAPHY_SIZE_BASE = '1rem'
GEOJSON_TYPOGRAPHY_SIZE_LG = '1.125rem'
GEOJSON_TYPOGRAPHY_SIZE_SM = '0.875rem'
GEOJSON_TYPOGRAPHY_SIZE_XL = '1.25rem'
GEOJSON_TYPOGRAPHY_SIZE_XS = '0.75rem'
GEOJSON_TYPOGRAPHY_WEIGHT_BOLD = 700
GEOJSON_TYPOGRAPHY_WEIGHT_MEDIUM = 500
GEOJSON_TYPOGRAPHY_WEIGHT_NORMAL = 400
GEOJSON_TYPOGRAPHY_WEIGHT_SEMIBOLD = 600

# ── radius ──
RADIUS_FULL = '9999px'
RADIUS_LG = '12px'
RADIUS_MD = '8px'
RADIUS_NONE = 0
RADIUS_SM = '4px'
RADIUS_XL = '16px'

# ── shadow ──
SHADOW_GLOW = '0 0 12px rgba(29,186,212,0.30)'
SHADOW_LG = '0 10px 25px rgba(0,0,0,0.5)'
SHADOW_MD = '0 4px 6px rgba(0,0,0,0.4)'
SHADOW_NONE = 'none'
SHADOW_SM = '0 1px 2px rgba(0,0,0,0.3)'
SHADOW_TEXT = '0 1px 3px rgba(0,0,0,0.7)'

# ── spacing ──
SPACING_0 = 0
SPACING_1 = '4px'
SPACING_10 = '40px'
SPACING_12 = '48px'
SPACING_16 = '64px'
SPACING_2 = '8px'
SPACING_3 = '12px'
SPACING_4 = '16px'
SPACING_5 = '20px'
SPACING_6 = '24px'
SPACING_8 = '32px'
SPACING_PX = '1px'

# ── typography ──
TYPOGRAPHY_FONT_FAMILY_MONO = "'SF Mono', 'Cascadia Code', 'Consolas', monospace"
TYPOGRAPHY_FONT_FAMILY_SANS = "system-ui, -apple-system, 'Microsoft YaHei', 'PingFang SC', sans-serif"
TYPOGRAPHY_FONT_SIZE_2XL = '1.5rem'
TYPOGRAPHY_FONT_SIZE_3XL = '2rem'
TYPOGRAPHY_FONT_SIZE_BASE = '0.875rem'
TYPOGRAPHY_FONT_SIZE_LG = '1rem'
TYPOGRAPHY_FONT_SIZE_SM = '0.75rem'
TYPOGRAPHY_FONT_SIZE_XL = '1.25rem'
TYPOGRAPHY_FONT_SIZE_XS = '0.625rem'
TYPOGRAPHY_FONT_WEIGHT_BOLD = 700
TYPOGRAPHY_FONT_WEIGHT_MEDIUM = 500
TYPOGRAPHY_FONT_WEIGHT_NORMAL = 400
TYPOGRAPHY_FONT_WEIGHT_SEMIBOLD = 600
TYPOGRAPHY_LETTER_SPACING_NORMAL = 0
TYPOGRAPHY_LETTER_SPACING_TIGHT = '-0.01em'
TYPOGRAPHY_LETTER_SPACING_WIDE = '0.02em'
TYPOGRAPHY_LINE_HEIGHT_NORMAL = 1.5
TYPOGRAPHY_LINE_HEIGHT_RELAXED = 1.75
TYPOGRAPHY_LINE_HEIGHT_TIGHT = 1.25

# ════════════════════════════════════════════════════════
#  Dark 主题 Token（向后兼容，默认值）
# ════════════════════════════════════════════════════════

# ── color ──
COLOR_BRAND_PRIMARY = '#48C9B0'
COLOR_BRAND_PRIMARY_ACTIVE = '#38B098'
COLOR_BRAND_PRIMARY_HOVER = '#5DD8C0'
COLOR_BRAND_SECONDARY = '#5DADE2'
COLOR_BRAND_SECONDARY_ACTIVE = '#4A9AD0'
COLOR_BRAND_SECONDARY_HOVER = '#7DBDE8'
COLOR_CHART_POLARITY_NEGATIVE = '#C4956A'
COLOR_CHART_POLARITY_NEUTRAL = '#C0C0C0'
COLOR_CHART_POLARITY_POSITIVE = '#5DADE2'
COLOR_CHART_POLARITY_VERY_NEGATIVE = '#B92D2D'
COLOR_CHART_POLARITY_VERY_POSITIVE = '#78DC32'
COLOR_EMOTION_NEGATIVE = '#D2AB8B'
COLOR_EMOTION_NEUTRAL = '#E6E6E6'
COLOR_EMOTION_POSITIVE = '#7FC0EC'
COLOR_EMOTION_VERY_NEGATIVE = '#B92D2D'
COLOR_EMOTION_VERY_POSITIVE = '#9CE365'
COLOR_FUNCTIONAL_BORDER_LIGHT = 'rgba(72,201,176,0.15)'
COLOR_FUNCTIONAL_BORDER_MEDIUM = 'rgba(72,201,176,0.22)'
COLOR_FUNCTIONAL_BORDER_STRONG = 'rgba(72,201,176,0.35)'
COLOR_FUNCTIONAL_DISABLED = '#585858'
COLOR_FUNCTIONAL_DISABLED_BG = 'rgba(88,88,88,0.25)'
COLOR_FUNCTIONAL_GLOW_CYAN = 'rgba(72,201,176,0.30)'
COLOR_FUNCTIONAL_LINK = '#5DADE2'
COLOR_FUNCTIONAL_OVERLAY_DARK = 'rgba(26,26,26,0.92)'
COLOR_FUNCTIONAL_OVERLAY_LIGHT = 'rgba(36,39,48,0.70)'
COLOR_FUNCTIONAL_OVERLAY_MEDIUM = 'rgba(36,39,48,0.85)'
COLOR_FUNCTIONAL_SELECTED = '#48C9B0'
COLOR_FUNCTIONAL_TEXT_ON_DARK = '#F0F0F0'
COLOR_FUNCTIONAL_TEXT_SECONDARY = '#C0C0C0'
COLOR_FUNCTIONAL_TEXT_TERTIARY = '#888888'
COLOR_GRADIENT_HOTCOLD0 = '#48C9B0'
COLOR_GRADIENT_HOTCOLD1 = '#5DADE2'
COLOR_GRADIENT_HOTCOLD2 = '#909090'
COLOR_GRADIENT_HOTCOLD3 = '#F0A050'
COLOR_GRADIENT_HOTCOLD4 = '#E06050'
COLOR_GRADIENT_NEG0 = '#641E16'
COLOR_GRADIENT_NEG1 = '#922B21'
COLOR_GRADIENT_NEG2 = '#C0392B'
COLOR_GRADIENT_NEG3 = '#E6B0AA'
COLOR_GRADIENT_NEG4 = '#FADBD8'
COLOR_GRADIENT_POS0 = '#0E6655'
COLOR_GRADIENT_POS1 = '#148F77'
COLOR_GRADIENT_POS2 = '#48C9B0'
COLOR_GRADIENT_POS3 = '#76D7C4'
COLOR_GRADIENT_POS4 = '#D1F2EB'
COLOR_NEUTRAL_0 = '#F0F0F0'
COLOR_NEUTRAL_100 = '#D0D0D0'
COLOR_NEUTRAL_200 = '#B0B0B0'
COLOR_NEUTRAL_300 = '#909090'
COLOR_NEUTRAL_400 = '#707070'
COLOR_NEUTRAL_50 = '#E0E0E0'
COLOR_NEUTRAL_500 = '#585858'
COLOR_NEUTRAL_600 = '#484848'
COLOR_NEUTRAL_700 = '#383838'
COLOR_NEUTRAL_800 = '#282828'
COLOR_NEUTRAL_900 = '#1A1A1A'
COLOR_SEMANTIC_ERROR = '#E06050'
COLOR_SEMANTIC_INFO = '#5DADE2'
COLOR_SEMANTIC_SUCCESS = '#48C9B0'
COLOR_SEMANTIC_WARNING = '#F0A050'

# ── component ──
COMPONENT_BADGE_BORDER_RADIUS = '12px'
COMPONENT_BADGE_FONT_SIZE = '0.65rem'
COMPONENT_BADGE_FONT_WEIGHT = 600
COMPONENT_BADGE_PADDING = '2px 8px'
COMPONENT_BADGE_TEXT_TRANSFORM = 'uppercase'
COMPONENT_BOUNDARY_COLOR = '#48C9B0'
COMPONENT_BOUNDARY_DASH_ARRAY = '6 3'
COMPONENT_BOUNDARY_FILL_OPACITY = 0.06
COMPONENT_BOUNDARY_WEIGHT = 2
COMPONENT_CHART_AXIS_COLOR = 'rgba(255,255,255,0.2)'
COMPONENT_CHART_BAR_COLOR = '#5DADE2'
COMPONENT_CHART_GRID_COLOR = 'rgba(255,255,255,0.06)'
COMPONENT_CHART_HEIGHT = 300
COMPONENT_CHART_LABEL_COLOR = '#888888'
COMPONENT_DATA_OVERLAY_BACKDROP_FILTER = 'blur(8px)'
COMPONENT_DATA_OVERLAY_BACKGROUND = 'rgba(36,39,48,0.82)'
COMPONENT_DATA_OVERLAY_BORDER = '1px solid rgba(29,186,212,0.15)'
COMPONENT_DATA_OVERLAY_BORDER_RADIUS = '8px'
COMPONENT_DATA_OVERLAY_COLOR = '#D0D0D0'
COMPONENT_DATA_OVERLAY_FONT_SIZE = '0.78rem'
COMPONENT_DATA_OVERLAY_LEFT = '14px'
COMPONENT_DATA_OVERLAY_LINE_HEIGHT = 1.5
COMPONENT_DATA_OVERLAY_PADDING = '5px 14px'
COMPONENT_DATA_OVERLAY_POINTER_EVENTS = 'none'
COMPONENT_DATA_OVERLAY_TOP = '54px'
COMPONENT_DATA_OVERLAY_Z_INDEX = 9999
COMPONENT_DATA_TABLE_BORDER_COLOR = 'rgba(72,201,176,0.12)'
COMPONENT_DATA_TABLE_CELL_PADDING = '6px 12px'
COMPONENT_DATA_TABLE_FONT_SIZE = '0.8rem'
COMPONENT_DATA_TABLE_HEADER_BACKGROUND = 'rgba(36,39,48,0.5)'
COMPONENT_DATA_TABLE_HEADER_COLOR = '#D0D0D0'
COMPONENT_DATA_TABLE_HEADER_FONT_WEIGHT = 600
COMPONENT_DATA_TABLE_ROW_HOVER_BACKGROUND = 'rgba(72,201,176,0.08)'
COMPONENT_DIALOG_BACKDROP_FILTER = 'blur(16px)'
COMPONENT_DIALOG_BACKGROUND = 'rgba(26,26,26,0.95)'
COMPONENT_DIALOG_BORDER = '1px solid rgba(29,186,212,0.2)'
COMPONENT_DIALOG_BORDER_RADIUS = '12px'
COMPONENT_DIALOG_COLOR = '#D0D0D0'
COMPONENT_DIALOG_DIVIDER_COLOR = '#3A3D48'
COMPONENT_DIALOG_FONT_SIZE = '1rem'
COMPONENT_DIALOG_LARGE_MAX_WIDTH = '800px'
COMPONENT_DIALOG_MAX_WIDTH = '600px'
COMPONENT_DIALOG_PADDING = '20px 32px'
COMPONENT_DIALOG_SMALL_MAX_WIDTH = '400px'
COMPONENT_DIALOG_TITLE_FONT_SIZE = '1.25rem'
COMPONENT_DIALOG_TITLE_FONT_WEIGHT = 600
COMPONENT_EMOTION_DOT_INNER_OPACITY = 0.92
COMPONENT_EMOTION_DOT_INNER_RADIUS = 7
COMPONENT_EMOTION_DOT_INNER_STROKE_COLOR = '#F0F0F0'
COMPONENT_EMOTION_DOT_INNER_STROKE_WIDTH = 2
COMPONENT_EMOTION_DOT_OUTER_OPACITY = 0.12
COMPONENT_EMOTION_DOT_OUTER_RADIUS = 13
COMPONENT_HUD_BUTTON_BACKDROP_FILTER = 'blur(8px)'
COMPONENT_HUD_BUTTON_BACKGROUND = 'rgba(36,39,48,0.85)'
COMPONENT_HUD_BUTTON_BORDER = '1px solid rgba(72,201,176,0.2)'
COMPONENT_HUD_BUTTON_BORDER_RADIUS = '10px'
COMPONENT_HUD_BUTTON_COLOR = '#D0D0D0'
COMPONENT_HUD_BUTTON_DISABLED_CURSOR = 'not-allowed'
COMPONENT_HUD_BUTTON_DISABLED_OPACITY = 0.4
COMPONENT_HUD_BUTTON_FONT_SIZE = '1.1rem'
COMPONENT_HUD_BUTTON_HEIGHT = '44px'
COMPONENT_HUD_BUTTON_HOVER_BACKGROUND = 'rgba(72,201,176,0.2)'
COMPONENT_HUD_BUTTON_TRANSITION = 'background 0.2s'
COMPONENT_HUD_BUTTON_WIDTH = '44px'
COMPONENT_HUD_BUTTON_Z_INDEX = 9999
COMPONENT_LEGEND_BACKDROP_FILTER = 'blur(4px)'
COMPONENT_LEGEND_BACKGROUND = 'rgba(36,39,48,0.88)'
COMPONENT_LEGEND_BORDER_RADIUS = '8px'
COMPONENT_LEGEND_BOTTOM = '12px'
COMPONENT_LEGEND_COLOR = '#D0D0D0'
COMPONENT_LEGEND_FONT_SIZE = '0.75rem'
COMPONENT_LEGEND_GRADIENT_BAR_HEIGHT = '10px'
COMPONENT_LEGEND_GRADIENT_BAR_WIDTH = '120px'
COMPONENT_LEGEND_LABEL_COLOR = '#888888'
COMPONENT_LEGEND_LABEL_FONT_SIZE = '0.7rem'
COMPONENT_LEGEND_LINE_HEIGHT = 1.6
COMPONENT_LEGEND_PADDING = '10px 14px'
COMPONENT_LEGEND_POINTER_EVENTS = 'none'
COMPONENT_LEGEND_RIGHT = '12px'
COMPONENT_LEGEND_TITLE_FONT_SIZE = '0.85rem'
COMPONENT_LEGEND_TITLE_FONT_WEIGHT = 700
COMPONENT_LEGEND_Z_INDEX = 9998
COMPONENT_SPINNER_COLOR = '#48C9B0'
COMPONENT_SPINNER_SIZE = '24px'
COMPONENT_SPINNER_THICKNESS = '3px'
COMPONENT_TITLE_BAR_BACKDROP_FILTER = 'blur(4px)'
COMPONENT_TITLE_BAR_BACKGROUND = 'rgba(36,39,48,0.75)'
COMPONENT_TITLE_BAR_BORDER_RADIUS = '20px'
COMPONENT_TITLE_BAR_COLOR = '#D0D0D0'
COMPONENT_TITLE_BAR_FONT_SIZE = '0.95rem'
COMPONENT_TITLE_BAR_FONT_WEIGHT = 600
COMPONENT_TITLE_BAR_PADDING = '4px 16px'
COMPONENT_TITLE_BAR_POINTER_EVENTS = 'none'
COMPONENT_TITLE_BAR_TEXT_SHADOW = '0 1px 3px rgba(0,0,0,0.7)'
COMPONENT_TITLE_BAR_TOP = '16px'
COMPONENT_TITLE_BAR_Z_INDEX = 9999
COMPONENT_TOAST_BACKDROP_FILTER = 'blur(8px)'
COMPONENT_TOAST_BACKGROUND = 'rgba(36,39,48,0.88)'
COMPONENT_TOAST_BORDER_RADIUS = '8px'
COMPONENT_TOAST_COLOR = '#D0D0D0'
COMPONENT_TOAST_ERROR_ICON_COLOR = '#E06050'
COMPONENT_TOAST_FONT_SIZE = '0.85rem'
COMPONENT_TOAST_PADDING = '10px 20px'
COMPONENT_TOAST_SUCCESS_ICON_COLOR = '#48C9B0'
COMPONENT_TOAST_WARNING_ICON_COLOR = '#F0A050'
COMPONENT_TOOLTIP_BACKDROP_FILTER = 'blur(8px)'
COMPONENT_TOOLTIP_BACKGROUND = 'rgba(26,26,26,0.92)'
COMPONENT_TOOLTIP_BORDER_RADIUS = '6px'
COMPONENT_TOOLTIP_COLOR = '#D0D0D0'
COMPONENT_TOOLTIP_FONT_SIZE = '0.75rem'
COMPONENT_TOOLTIP_MAX_WIDTH = '300px'
COMPONENT_TOOLTIP_PADDING = '6px 10px'

# ── 便捷聚合 ──

COLOR = {
    'color-brand-primary': COLOR_BRAND_PRIMARY,
    'color-brand-primary-active': COLOR_BRAND_PRIMARY_ACTIVE,
    'color-brand-primary-hover': COLOR_BRAND_PRIMARY_HOVER,
    'color-brand-secondary': COLOR_BRAND_SECONDARY,
    'color-brand-secondary-active': COLOR_BRAND_SECONDARY_ACTIVE,
    'color-brand-secondary-hover': COLOR_BRAND_SECONDARY_HOVER,
    'color-chart-polarity-negative': COLOR_CHART_POLARITY_NEGATIVE,
    'color-chart-polarity-neutral': COLOR_CHART_POLARITY_NEUTRAL,
    'color-chart-polarity-positive': COLOR_CHART_POLARITY_POSITIVE,
    'color-chart-polarity-very-negative': COLOR_CHART_POLARITY_VERY_NEGATIVE,
    'color-chart-polarity-very-positive': COLOR_CHART_POLARITY_VERY_POSITIVE,
    'color-emotion-negative': COLOR_EMOTION_NEGATIVE,
    'color-emotion-neutral': COLOR_EMOTION_NEUTRAL,
    'color-emotion-positive': COLOR_EMOTION_POSITIVE,
    'color-emotion-very-negative': COLOR_EMOTION_VERY_NEGATIVE,
    'color-emotion-very-positive': COLOR_EMOTION_VERY_POSITIVE,
    'color-functional-border-light': COLOR_FUNCTIONAL_BORDER_LIGHT,
    'color-functional-border-medium': COLOR_FUNCTIONAL_BORDER_MEDIUM,
    'color-functional-border-strong': COLOR_FUNCTIONAL_BORDER_STRONG,
    'color-functional-disabled': COLOR_FUNCTIONAL_DISABLED,
    'color-functional-disabled-bg': COLOR_FUNCTIONAL_DISABLED_BG,
    'color-functional-glow-cyan': COLOR_FUNCTIONAL_GLOW_CYAN,
    'color-functional-link': COLOR_FUNCTIONAL_LINK,
    'color-functional-overlay-dark': COLOR_FUNCTIONAL_OVERLAY_DARK,
    'color-functional-overlay-light': COLOR_FUNCTIONAL_OVERLAY_LIGHT,
    'color-functional-overlay-medium': COLOR_FUNCTIONAL_OVERLAY_MEDIUM,
    'color-functional-selected': COLOR_FUNCTIONAL_SELECTED,
    'color-functional-text-on-dark': COLOR_FUNCTIONAL_TEXT_ON_DARK,
    'color-functional-text-secondary': COLOR_FUNCTIONAL_TEXT_SECONDARY,
    'color-functional-text-tertiary': COLOR_FUNCTIONAL_TEXT_TERTIARY,
    'color-gradient-hotcold0': COLOR_GRADIENT_HOTCOLD0,
    'color-gradient-hotcold1': COLOR_GRADIENT_HOTCOLD1,
    'color-gradient-hotcold2': COLOR_GRADIENT_HOTCOLD2,
    'color-gradient-hotcold3': COLOR_GRADIENT_HOTCOLD3,
    'color-gradient-hotcold4': COLOR_GRADIENT_HOTCOLD4,
    'color-gradient-neg0': COLOR_GRADIENT_NEG0,
    'color-gradient-neg1': COLOR_GRADIENT_NEG1,
    'color-gradient-neg2': COLOR_GRADIENT_NEG2,
    'color-gradient-neg3': COLOR_GRADIENT_NEG3,
    'color-gradient-neg4': COLOR_GRADIENT_NEG4,
    'color-gradient-pos0': COLOR_GRADIENT_POS0,
    'color-gradient-pos1': COLOR_GRADIENT_POS1,
    'color-gradient-pos2': COLOR_GRADIENT_POS2,
    'color-gradient-pos3': COLOR_GRADIENT_POS3,
    'color-gradient-pos4': COLOR_GRADIENT_POS4,
    'color-neutral-0': COLOR_NEUTRAL_0,
    'color-neutral-100': COLOR_NEUTRAL_100,
    'color-neutral-200': COLOR_NEUTRAL_200,
    'color-neutral-300': COLOR_NEUTRAL_300,
    'color-neutral-400': COLOR_NEUTRAL_400,
    'color-neutral-50': COLOR_NEUTRAL_50,
    'color-neutral-500': COLOR_NEUTRAL_500,
    'color-neutral-600': COLOR_NEUTRAL_600,
    'color-neutral-700': COLOR_NEUTRAL_700,
    'color-neutral-800': COLOR_NEUTRAL_800,
    'color-neutral-900': COLOR_NEUTRAL_900,
    'color-semantic-error': COLOR_SEMANTIC_ERROR,
    'color-semantic-info': COLOR_SEMANTIC_INFO,
    'color-semantic-success': COLOR_SEMANTIC_SUCCESS,
    'color-semantic-warning': COLOR_SEMANTIC_WARNING,
}

SPACING = {
}

RADIUS = {
}

EMOTION_COLORS = {
    'negative': COLOR_EMOTION_NEGATIVE,
    'neutral': COLOR_EMOTION_NEUTRAL,
    'positive': COLOR_EMOTION_POSITIVE,
    'very-negative': COLOR_EMOTION_VERY_NEGATIVE,
    'very-positive': COLOR_EMOTION_VERY_POSITIVE,
}

# ════════════════════════════════════════════════════════
#  Light/Dark 双主题字典
# ════════════════════════════════════════════════════════

DARK_TOKENS = {
    'color-brand-primary': '#48C9B0',
    'color-brand-primary-active': '#38B098',
    'color-brand-primary-hover': '#5DD8C0',
    'color-brand-secondary': '#5DADE2',
    'color-brand-secondary-active': '#4A9AD0',
    'color-brand-secondary-hover': '#7DBDE8',
    'color-chart-polarity-negative': '#C4956A',
    'color-chart-polarity-neutral': '#C0C0C0',
    'color-chart-polarity-positive': '#5DADE2',
    'color-chart-polarity-very-negative': '#B92D2D',
    'color-chart-polarity-very-positive': '#78DC32',
    'color-emotion-negative': '#D2AB8B',
    'color-emotion-neutral': '#E6E6E6',
    'color-emotion-positive': '#7FC0EC',
    'color-emotion-very-negative': '#B92D2D',
    'color-emotion-very-positive': '#9CE365',
    'color-functional-border-light': 'rgba(72,201,176,0.15)',
    'color-functional-border-medium': 'rgba(72,201,176,0.22)',
    'color-functional-border-strong': 'rgba(72,201,176,0.35)',
    'color-functional-disabled': '#585858',
    'color-functional-disabled-bg': 'rgba(88,88,88,0.25)',
    'color-functional-glow-cyan': 'rgba(72,201,176,0.30)',
    'color-functional-link': '#5DADE2',
    'color-functional-overlay-dark': 'rgba(26,26,26,0.92)',
    'color-functional-overlay-light': 'rgba(36,39,48,0.70)',
    'color-functional-overlay-medium': 'rgba(36,39,48,0.85)',
    'color-functional-selected': '#48C9B0',
    'color-functional-text-on-dark': '#F0F0F0',
    'color-functional-text-secondary': '#C0C0C0',
    'color-functional-text-tertiary': '#888888',
    'color-gradient-hotcold0': '#48C9B0',
    'color-gradient-hotcold1': '#5DADE2',
    'color-gradient-hotcold2': '#909090',
    'color-gradient-hotcold3': '#F0A050',
    'color-gradient-hotcold4': '#E06050',
    'color-gradient-neg0': '#641E16',
    'color-gradient-neg1': '#922B21',
    'color-gradient-neg2': '#C0392B',
    'color-gradient-neg3': '#E6B0AA',
    'color-gradient-neg4': '#FADBD8',
    'color-gradient-pos0': '#0E6655',
    'color-gradient-pos1': '#148F77',
    'color-gradient-pos2': '#48C9B0',
    'color-gradient-pos3': '#76D7C4',
    'color-gradient-pos4': '#D1F2EB',
    'color-neutral-0': '#F0F0F0',
    'color-neutral-100': '#D0D0D0',
    'color-neutral-200': '#B0B0B0',
    'color-neutral-300': '#909090',
    'color-neutral-400': '#707070',
    'color-neutral-50': '#E0E0E0',
    'color-neutral-500': '#585858',
    'color-neutral-600': '#484848',
    'color-neutral-700': '#383838',
    'color-neutral-800': '#282828',
    'color-neutral-900': '#1A1A1A',
    'color-semantic-error': '#E06050',
    'color-semantic-info': '#5DADE2',
    'color-semantic-success': '#48C9B0',
    'color-semantic-warning': '#F0A050',
    'component-badge-border-radius': '12px',
    'component-badge-font-size': '0.65rem',
    'component-badge-font-weight': 600,
    'component-badge-padding': '2px 8px',
    'component-badge-text-transform': 'uppercase',
    'component-boundary-color': '#48C9B0',
    'component-boundary-dash-array': '6 3',
    'component-boundary-fill-opacity': 0.06,
    'component-boundary-weight': 2,
    'component-chart-axis-color': 'rgba(255,255,255,0.2)',
    'component-chart-bar-color': '#5DADE2',
    'component-chart-grid-color': 'rgba(255,255,255,0.06)',
    'component-chart-height': 300,
    'component-chart-label-color': '#888888',
    'component-data-overlay-backdrop-filter': 'blur(8px)',
    'component-data-overlay-background': 'rgba(36,39,48,0.82)',
    'component-data-overlay-border': '1px solid rgba(29,186,212,0.15)',
    'component-data-overlay-border-radius': '8px',
    'component-data-overlay-color': '#D0D0D0',
    'component-data-overlay-font-size': '0.78rem',
    'component-data-overlay-left': '14px',
    'component-data-overlay-line-height': 1.5,
    'component-data-overlay-padding': '5px 14px',
    'component-data-overlay-pointer-events': 'none',
    'component-data-overlay-top': '54px',
    'component-data-overlay-z-index': 9999,
    'component-data-table-border-color': 'rgba(72,201,176,0.12)',
    'component-data-table-cell-padding': '6px 12px',
    'component-data-table-font-size': '0.8rem',
    'component-data-table-header-background': 'rgba(36,39,48,0.5)',
    'component-data-table-header-color': '#D0D0D0',
    'component-data-table-header-font-weight': 600,
    'component-data-table-row-hover-background': 'rgba(72,201,176,0.08)',
    'component-dialog-backdrop-filter': 'blur(16px)',
    'component-dialog-background': 'rgba(26,26,26,0.95)',
    'component-dialog-border': '1px solid rgba(29,186,212,0.2)',
    'component-dialog-border-radius': '12px',
    'component-dialog-color': '#D0D0D0',
    'component-dialog-divider-color': '#3A3D48',
    'component-dialog-font-size': '1rem',
    'component-dialog-large-max-width': '800px',
    'component-dialog-max-width': '600px',
    'component-dialog-padding': '20px 32px',
    'component-dialog-small-max-width': '400px',
    'component-dialog-title-font-size': '1.25rem',
    'component-dialog-title-font-weight': 600,
    'component-emotion-dot-inner-opacity': 0.92,
    'component-emotion-dot-inner-radius': 7,
    'component-emotion-dot-inner-stroke-color': '#F0F0F0',
    'component-emotion-dot-inner-stroke-width': 2,
    'component-emotion-dot-outer-opacity': 0.12,
    'component-emotion-dot-outer-radius': 13,
    'component-hud-button-backdrop-filter': 'blur(8px)',
    'component-hud-button-background': 'rgba(36,39,48,0.85)',
    'component-hud-button-border': '1px solid rgba(72,201,176,0.2)',
    'component-hud-button-border-radius': '10px',
    'component-hud-button-color': '#D0D0D0',
    'component-hud-button-disabled-cursor': 'not-allowed',
    'component-hud-button-disabled-opacity': 0.4,
    'component-hud-button-font-size': '1.1rem',
    'component-hud-button-height': '44px',
    'component-hud-button-hover-background': 'rgba(72,201,176,0.2)',
    'component-hud-button-transition': 'background 0.2s',
    'component-hud-button-width': '44px',
    'component-hud-button-z-index': 9999,
    'component-legend-backdrop-filter': 'blur(4px)',
    'component-legend-background': 'rgba(36,39,48,0.88)',
    'component-legend-border-radius': '8px',
    'component-legend-bottom': '12px',
    'component-legend-color': '#D0D0D0',
    'component-legend-font-size': '0.75rem',
    'component-legend-gradient-bar-height': '10px',
    'component-legend-gradient-bar-width': '120px',
    'component-legend-label-color': '#888888',
    'component-legend-label-font-size': '0.7rem',
    'component-legend-line-height': 1.6,
    'component-legend-padding': '10px 14px',
    'component-legend-pointer-events': 'none',
    'component-legend-right': '12px',
    'component-legend-title-font-size': '0.85rem',
    'component-legend-title-font-weight': 700,
    'component-legend-z-index': 9998,
    'component-spinner-color': '#48C9B0',
    'component-spinner-size': '24px',
    'component-spinner-thickness': '3px',
    'component-title-bar-backdrop-filter': 'blur(4px)',
    'component-title-bar-background': 'rgba(36,39,48,0.75)',
    'component-title-bar-border-radius': '20px',
    'component-title-bar-color': '#D0D0D0',
    'component-title-bar-font-size': '0.95rem',
    'component-title-bar-font-weight': 600,
    'component-title-bar-padding': '4px 16px',
    'component-title-bar-pointer-events': 'none',
    'component-title-bar-text-shadow': '0 1px 3px rgba(0,0,0,0.7)',
    'component-title-bar-top': '16px',
    'component-title-bar-z-index': 9999,
    'component-toast-backdrop-filter': 'blur(8px)',
    'component-toast-background': 'rgba(36,39,48,0.88)',
    'component-toast-border-radius': '8px',
    'component-toast-color': '#D0D0D0',
    'component-toast-error-icon-color': '#E06050',
    'component-toast-font-size': '0.85rem',
    'component-toast-padding': '10px 20px',
    'component-toast-success-icon-color': '#48C9B0',
    'component-toast-warning-icon-color': '#F0A050',
    'component-tooltip-backdrop-filter': 'blur(8px)',
    'component-tooltip-background': 'rgba(26,26,26,0.92)',
    'component-tooltip-border-radius': '6px',
    'component-tooltip-color': '#D0D0D0',
    'component-tooltip-font-size': '0.75rem',
    'component-tooltip-max-width': '300px',
    'component-tooltip-padding': '6px 10px',
}

LIGHT_TOKENS = {
    'color-brand-primary': '#16A085',
    'color-brand-primary-active': '#0E7A6A',
    'color-brand-primary-hover': '#48C9B0',
    'color-brand-secondary': '#2980B9',
    'color-brand-secondary-active': '#1E6BA0',
    'color-brand-secondary-hover': '#5DADE2',
    'color-chart-polarity-negative': '#C4956A',
    'color-chart-polarity-neutral': '#C0C0C0',
    'color-chart-polarity-positive': '#5DADE2',
    'color-chart-polarity-very-negative': '#B92D2D',
    'color-chart-polarity-very-positive': '#78DC32',
    'color-emotion-negative': '#D68910',
    'color-emotion-neutral': '#888888',
    'color-emotion-positive': '#2980B9',
    'color-emotion-very-negative': '#C0392B',
    'color-emotion-very-positive': '#16A085',
    'color-functional-border-light': 'rgba(22,160,133,0.15)',
    'color-functional-border-medium': 'rgba(22,160,133,0.22)',
    'color-functional-border-strong': 'rgba(22,160,133,0.35)',
    'color-functional-disabled': '#B0B0B0',
    'color-functional-disabled-bg': 'rgba(150,150,150,0.15)',
    'color-functional-glow-cyan': 'rgba(72,201,176,0.2)',
    'color-functional-link': '#2980B9',
    'color-functional-overlay-dark': 'rgba(255,255,255,0.88)',
    'color-functional-overlay-light': 'rgba(255,255,255,0.65)',
    'color-functional-overlay-medium': 'rgba(255,255,255,0.78)',
    'color-functional-selected': '#48C9B0',
    'color-functional-text-on-dark': '#1A1A1A',
    'color-functional-text-secondary': '#585858',
    'color-functional-text-tertiary': '#808080',
    'color-gradient-hotcold0': '#16A085',
    'color-gradient-hotcold1': '#2980B9',
    'color-gradient-hotcold2': '#909090',
    'color-gradient-hotcold3': '#D68910',
    'color-gradient-hotcold4': '#C0392B',
    'color-gradient-neg0': '#641E16',
    'color-gradient-neg1': '#922B21',
    'color-gradient-neg2': '#C0392B',
    'color-gradient-neg3': '#E6B0AA',
    'color-gradient-neg4': '#FADBD8',
    'color-gradient-pos0': '#0A5344',
    'color-gradient-pos1': '#117A65',
    'color-gradient-pos2': '#16A085',
    'color-gradient-pos3': '#48C9B0',
    'color-gradient-pos4': '#A3E4D7',
    'color-neutral-0': '#FFFFFF',
    'color-neutral-100': '#E8E8E8',
    'color-neutral-200': '#D0D0D0',
    'color-neutral-300': '#B0B0B0',
    'color-neutral-400': '#909090',
    'color-neutral-50': '#F5F5F5',
    'color-neutral-500': '#707070',
    'color-neutral-600': '#585858',
    'color-neutral-700': '#404040',
    'color-neutral-800': '#2A2A2A',
    'color-neutral-900': '#1A1A1A',
    'color-semantic-error': '#C0392B',
    'color-semantic-info': '#2980B9',
    'color-semantic-success': '#16A085',
    'color-semantic-warning': '#D68910',
    'component-badge-border-radius': '12px',
    'component-badge-font-size': '0.65rem',
    'component-badge-font-weight': 600,
    'component-badge-padding': '2px 8px',
    'component-badge-text-transform': 'uppercase',
    'component-boundary-color': '#16A085',
    'component-boundary-dash-array': '6 3',
    'component-boundary-fill-opacity': 0.06,
    'component-boundary-weight': 2,
    'component-chart-axis-color': 'rgba(0,0,0,0.15)',
    'component-chart-bar-color': '#2980B9',
    'component-chart-grid-color': 'rgba(0,0,0,0.06)',
    'component-chart-height': 300,
    'component-chart-label-color': '#808080',
    'component-data-overlay-backdrop-filter': 'blur(8px)',
    'component-data-overlay-background': 'rgba(255,255,255,0.88)',
    'component-data-overlay-border': '1px solid rgba(22,160,133,0.12)',
    'component-data-overlay-border-radius': '8px',
    'component-data-overlay-color': '#2A2A2A',
    'component-data-overlay-font-size': '0.78rem',
    'component-data-overlay-left': '14px',
    'component-data-overlay-line-height': 1.5,
    'component-data-overlay-padding': '5px 14px',
    'component-data-overlay-pointer-events': 'none',
    'component-data-overlay-top': '54px',
    'component-data-overlay-z-index': 9999,
    'component-data-table-border-color': 'rgba(22,160,133,0.12)',
    'component-data-table-cell-padding': '6px 12px',
    'component-data-table-font-size': '0.8rem',
    'component-data-table-header-background': 'rgba(22,160,133,0.06)',
    'component-data-table-header-color': '#2A2A2A',
    'component-data-table-header-font-weight': 600,
    'component-data-table-row-hover-background': 'rgba(72,201,176,0.06)',
    'component-dialog-backdrop-filter': 'blur(16px)',
    'component-dialog-background': 'rgba(255,255,255,0.94)',
    'component-dialog-border': '1px solid rgba(22,160,133,0.2)',
    'component-dialog-border-radius': '12px',
    'component-dialog-color': '#2A2A2A',
    'component-dialog-divider-color': '#E0E0E0',
    'component-dialog-font-size': '1rem',
    'component-dialog-large-max-width': '800px',
    'component-dialog-max-width': '600px',
    'component-dialog-padding': '20px 32px',
    'component-dialog-small-max-width': '400px',
    'component-dialog-title-font-size': '1.25rem',
    'component-dialog-title-font-weight': 600,
    'component-emotion-dot-inner-opacity': 0.92,
    'component-emotion-dot-inner-radius': 7,
    'component-emotion-dot-inner-stroke-color': '#FFFFFF',
    'component-emotion-dot-inner-stroke-width': 2,
    'component-emotion-dot-outer-opacity': 0.18,
    'component-emotion-dot-outer-radius': 13,
    'component-hud-button-backdrop-filter': 'blur(8px)',
    'component-hud-button-background': 'rgba(255,255,255,0.88)',
    'component-hud-button-border': '1px solid rgba(22,160,133,0.25)',
    'component-hud-button-border-radius': '10px',
    'component-hud-button-color': '#2A2A2A',
    'component-hud-button-disabled-cursor': 'not-allowed',
    'component-hud-button-disabled-opacity': 0.35,
    'component-hud-button-font-size': '1.1rem',
    'component-hud-button-height': '44px',
    'component-hud-button-hover-background': 'rgba(72,201,176,0.12)',
    'component-hud-button-transition': 'background 0.2s',
    'component-hud-button-width': '44px',
    'component-hud-button-z-index': 9999,
    'component-legend-backdrop-filter': 'blur(4px)',
    'component-legend-background': 'rgba(255,255,255,0.88)',
    'component-legend-border-radius': '8px',
    'component-legend-bottom': '12px',
    'component-legend-color': '#2A2A2A',
    'component-legend-font-size': '0.75rem',
    'component-legend-gradient-bar-height': '10px',
    'component-legend-gradient-bar-width': '120px',
    'component-legend-label-color': '#808080',
    'component-legend-label-font-size': '0.7rem',
    'component-legend-line-height': 1.6,
    'component-legend-padding': '10px 14px',
    'component-legend-pointer-events': 'none',
    'component-legend-right': '12px',
    'component-legend-title-font-size': '0.85rem',
    'component-legend-title-font-weight': 700,
    'component-legend-z-index': 9998,
    'component-spinner-color': '#16A085',
    'component-spinner-size': '24px',
    'component-spinner-thickness': '3px',
    'component-title-bar-backdrop-filter': 'blur(4px)',
    'component-title-bar-background': 'rgba(255,255,255,0.78)',
    'component-title-bar-border-radius': '20px',
    'component-title-bar-color': '#2A2A2A',
    'component-title-bar-font-size': '0.95rem',
    'component-title-bar-font-weight': 600,
    'component-title-bar-padding': '4px 16px',
    'component-title-bar-pointer-events': 'none',
    'component-title-bar-text-shadow': 'none',
    'component-title-bar-top': '16px',
    'component-title-bar-z-index': 9999,
    'component-toast-backdrop-filter': 'blur(8px)',
    'component-toast-background': 'rgba(42,42,42,0.92)',
    'component-toast-border-radius': '8px',
    'component-toast-color': '#F0F0F0',
    'component-toast-error-icon-color': '#C0392B',
    'component-toast-font-size': '0.85rem',
    'component-toast-padding': '10px 20px',
    'component-toast-success-icon-color': '#16A085',
    'component-toast-warning-icon-color': '#D68910',
    'component-tooltip-backdrop-filter': 'blur(8px)',
    'component-tooltip-background': 'rgba(42,42,42,0.94)',
    'component-tooltip-border-radius': '6px',
    'component-tooltip-color': '#F0F0F0',
    'component-tooltip-font-size': '0.75rem',
    'component-tooltip-max-width': '300px',
    'component-tooltip-padding': '6px 10px',
}


def get_token(name: str, theme: str = 'dark') -> str:
    """获取指定主题的 token 值。

    参数:
        name: token 名称，如 'color-brand-primary', 'component-hud-button-background'
        theme: 'dark' | 'light'

    返回:
        token 字符串值；如未找到则返回空字符串

    示例:
        get_token('color-brand-primary', 'light')  # '#ff6b35'
        get_token('component-dialog-background', 'dark')  # 'rgba(0,0,0,0.55)'
    """
    if theme == 'light':
        return LIGHT_TOKENS.get(name, '')
    return DARK_TOKENS.get(name, '')
