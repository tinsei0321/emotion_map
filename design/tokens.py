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

# ── radius ──
RADIUS_FULL = '9999px'
RADIUS_LG = '12px'
RADIUS_MD = '8px'
RADIUS_NONE = 0
RADIUS_SM = '4px'
RADIUS_XL = '16px'

# ── shadow ──
SHADOW_GLOW = '0 0 12px rgba(217,125,92,0.35)'
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
COLOR_BRAND_PRIMARY = '#d97d5c'
COLOR_BRAND_PRIMARY_ACTIVE = '#ae5f43'
COLOR_BRAND_PRIMARY_HOVER = '#c46e4f'
COLOR_BRAND_SECONDARY = '#7ba4cc'
COLOR_BRAND_SECONDARY_ACTIVE = '#5c84a8'
COLOR_BRAND_SECONDARY_HOVER = '#6b94ba'
COLOR_CHART_POLARITY_NEGATIVE = '#d9805c'
COLOR_CHART_POLARITY_NEUTRAL = '#8a8a8a'
COLOR_CHART_POLARITY_POSITIVE = '#5aab8a'
COLOR_CHART_POLARITY_VERY_NEGATIVE = '#cc6b6b'
COLOR_CHART_POLARITY_VERY_POSITIVE = '#3d8c6e'
COLOR_EMOTION_NEGATIVE = '#d9805c'
COLOR_EMOTION_NEUTRAL = '#c4a855'
COLOR_EMOTION_POSITIVE = '#8fbf9f'
COLOR_EMOTION_VERY_NEGATIVE = '#cc6b6b'
COLOR_EMOTION_VERY_POSITIVE = '#5aab8a'
COLOR_FUNCTIONAL_BORDER_LIGHT = 'rgba(255,255,255,0.12)'
COLOR_FUNCTIONAL_BORDER_MEDIUM = 'rgba(255,255,255,0.15)'
COLOR_FUNCTIONAL_BORDER_STRONG = 'rgba(255,255,255,0.25)'
COLOR_FUNCTIONAL_DISABLED = '#737373'
COLOR_FUNCTIONAL_DISABLED_BG = 'rgba(115,115,115,0.25)'
COLOR_FUNCTIONAL_GLOW_ORANGE = 'rgba(217,125,92,0.35)'
COLOR_FUNCTIONAL_LINK = '#7ba4cc'
COLOR_FUNCTIONAL_OVERLAY_DARK = 'rgba(0,0,0,0.55)'
COLOR_FUNCTIONAL_OVERLAY_LIGHT = 'rgba(0,0,0,0.40)'
COLOR_FUNCTIONAL_OVERLAY_MEDIUM = 'rgba(0,0,0,0.45)'
COLOR_FUNCTIONAL_SELECTED = '#d97d5c'
COLOR_FUNCTIONAL_TEXT_ON_DARK = '#ffffff'
COLOR_FUNCTIONAL_TEXT_SECONDARY = '#cccccc'
COLOR_FUNCTIONAL_TEXT_TERTIARY = '#aaaaaa'
COLOR_GRADIENT_HOTCOLD0 = '#b8d4e3'
COLOR_GRADIENT_HOTCOLD1 = '#e8e0b0'
COLOR_GRADIENT_HOTCOLD2 = '#d9ac7c'
COLOR_GRADIENT_HOTCOLD3 = '#d9886b'
COLOR_GRADIENT_HOTCOLD4 = '#b85c4a'
COLOR_GRADIENT_NEG0 = '#252525'
COLOR_GRADIENT_NEG1 = '#636363'
COLOR_GRADIENT_NEG2 = '#bdbdbd'
COLOR_GRADIENT_NEG3 = '#f0f0f0'
COLOR_GRADIENT_NEG4 = '#f0edc5'
COLOR_GRADIENT_POS0 = '#004529'
COLOR_GRADIENT_POS1 = '#3d8c5e'
COLOR_GRADIENT_POS2 = '#5aab8a'
COLOR_GRADIENT_POS3 = '#a3d4b5'
COLOR_GRADIENT_POS4 = '#f0edc5'
COLOR_NEUTRAL_0 = '#ffffff'
COLOR_NEUTRAL_100 = '#f5f5f5'
COLOR_NEUTRAL_200 = '#e5e5e5'
COLOR_NEUTRAL_300 = '#d4d4d4'
COLOR_NEUTRAL_400 = '#a3a3a3'
COLOR_NEUTRAL_50 = '#fafafa'
COLOR_NEUTRAL_500 = '#737373'
COLOR_NEUTRAL_600 = '#525252'
COLOR_NEUTRAL_700 = '#404040'
COLOR_NEUTRAL_800 = '#262626'
COLOR_NEUTRAL_900 = '#1a1a1a'
COLOR_SEMANTIC_ERROR = '#d4645c'
COLOR_SEMANTIC_INFO = '#7ba4cc'
COLOR_SEMANTIC_SUCCESS = '#4d9e6c'
COLOR_SEMANTIC_WARNING = '#d4a33a'

# ── component ──
COMPONENT_BADGE_BORDER_RADIUS = '12px'
COMPONENT_BADGE_FONT_SIZE = '0.65rem'
COMPONENT_BADGE_FONT_WEIGHT = 600
COMPONENT_BADGE_PADDING = '2px 8px'
COMPONENT_BADGE_TEXT_TRANSFORM = 'uppercase'
COMPONENT_BOUNDARY_COLOR = '#d97d5c'
COMPONENT_BOUNDARY_DASH_ARRAY = '6 3'
COMPONENT_BOUNDARY_FILL_OPACITY = 0.08
COMPONENT_BOUNDARY_WEIGHT = 2
COMPONENT_CHART_AXIS_COLOR = 'rgba(255,255,255,0.3)'
COMPONENT_CHART_BAR_COLOR = '#7ba4cc'
COMPONENT_CHART_GRID_COLOR = 'rgba(255,255,255,0.1)'
COMPONENT_CHART_HEIGHT = 300
COMPONENT_CHART_LABEL_COLOR = '#aaaaaa'
COMPONENT_DATA_OVERLAY_BACKDROP_FILTER = 'blur(8px)'
COMPONENT_DATA_OVERLAY_BACKGROUND = 'rgba(0,0,0,0.45)'
COMPONENT_DATA_OVERLAY_BORDER = '1px solid rgba(255,255,255,0.10)'
COMPONENT_DATA_OVERLAY_BORDER_RADIUS = '8px'
COMPONENT_DATA_OVERLAY_COLOR = '#ffffff'
COMPONENT_DATA_OVERLAY_FONT_SIZE = '0.78rem'
COMPONENT_DATA_OVERLAY_LEFT = '14px'
COMPONENT_DATA_OVERLAY_LINE_HEIGHT = 1.5
COMPONENT_DATA_OVERLAY_PADDING = '5px 14px'
COMPONENT_DATA_OVERLAY_POINTER_EVENTS = 'none'
COMPONENT_DATA_OVERLAY_TOP = '54px'
COMPONENT_DATA_OVERLAY_Z_INDEX = 9999
COMPONENT_DATA_TABLE_BORDER_COLOR = 'rgba(255,255,255,0.08)'
COMPONENT_DATA_TABLE_CELL_PADDING = '6px 12px'
COMPONENT_DATA_TABLE_FONT_SIZE = '0.8rem'
COMPONENT_DATA_TABLE_HEADER_BACKGROUND = 'rgba(0,0,0,0.3)'
COMPONENT_DATA_TABLE_HEADER_COLOR = '#ffffff'
COMPONENT_DATA_TABLE_HEADER_FONT_WEIGHT = 600
COMPONENT_DATA_TABLE_ROW_HOVER_BACKGROUND = 'rgba(217,125,92,0.08)'
COMPONENT_DIALOG_BACKDROP_FILTER = 'blur(12px)'
COMPONENT_DIALOG_BACKGROUND = 'rgba(0,0,0,0.55)'
COMPONENT_DIALOG_BORDER = '1px solid rgba(255,255,255,0.12)'
COMPONENT_DIALOG_BORDER_RADIUS = '12px'
COMPONENT_DIALOG_COLOR = '#ffffff'
COMPONENT_DIALOG_DIVIDER_COLOR = '#404040'
COMPONENT_DIALOG_FONT_SIZE = '1rem'
COMPONENT_DIALOG_LARGE_MAX_WIDTH = '800px'
COMPONENT_DIALOG_MAX_WIDTH = '600px'
COMPONENT_DIALOG_PADDING = '20px 32px'
COMPONENT_DIALOG_SMALL_MAX_WIDTH = '400px'
COMPONENT_DIALOG_TITLE_FONT_SIZE = '1.25rem'
COMPONENT_DIALOG_TITLE_FONT_WEIGHT = 600
COMPONENT_EMOTION_DOT_INNER_OPACITY = 0.92
COMPONENT_EMOTION_DOT_INNER_RADIUS = 7
COMPONENT_EMOTION_DOT_INNER_STROKE_COLOR = '#ffffff'
COMPONENT_EMOTION_DOT_INNER_STROKE_WIDTH = 2
COMPONENT_EMOTION_DOT_OUTER_OPACITY = 0.12
COMPONENT_EMOTION_DOT_OUTER_RADIUS = 13
COMPONENT_HUD_BUTTON_BACKDROP_FILTER = 'blur(8px)'
COMPONENT_HUD_BUTTON_BACKGROUND = 'rgba(30,30,30,0.75)'
COMPONENT_HUD_BUTTON_BORDER = '1px solid rgba(255,255,255,0.15)'
COMPONENT_HUD_BUTTON_BORDER_RADIUS = '10px'
COMPONENT_HUD_BUTTON_COLOR = '#ffffff'
COMPONENT_HUD_BUTTON_DISABLED_CURSOR = 'not-allowed'
COMPONENT_HUD_BUTTON_DISABLED_OPACITY = 0.4
COMPONENT_HUD_BUTTON_FONT_SIZE = '1.1rem'
COMPONENT_HUD_BUTTON_HEIGHT = '44px'
COMPONENT_HUD_BUTTON_HOVER_BACKGROUND = 'rgba(217,125,92,0.25)'
COMPONENT_HUD_BUTTON_TRANSITION = 'background 0.2s'
COMPONENT_HUD_BUTTON_WIDTH = '44px'
COMPONENT_HUD_BUTTON_Z_INDEX = 9999
COMPONENT_LEGEND_BACKDROP_FILTER = 'blur(4px)'
COMPONENT_LEGEND_BACKGROUND = 'rgba(0,0,0,0.6)'
COMPONENT_LEGEND_BORDER_RADIUS = '8px'
COMPONENT_LEGEND_BOTTOM = '12px'
COMPONENT_LEGEND_COLOR = '#ffffff'
COMPONENT_LEGEND_FONT_SIZE = '0.75rem'
COMPONENT_LEGEND_GRADIENT_BAR_HEIGHT = '10px'
COMPONENT_LEGEND_GRADIENT_BAR_WIDTH = '120px'
COMPONENT_LEGEND_LABEL_COLOR = '#aaaaaa'
COMPONENT_LEGEND_LABEL_FONT_SIZE = '0.7rem'
COMPONENT_LEGEND_LINE_HEIGHT = 1.6
COMPONENT_LEGEND_PADDING = '10px 14px'
COMPONENT_LEGEND_POINTER_EVENTS = 'none'
COMPONENT_LEGEND_RIGHT = '12px'
COMPONENT_LEGEND_TITLE_FONT_SIZE = '0.85rem'
COMPONENT_LEGEND_TITLE_FONT_WEIGHT = 700
COMPONENT_LEGEND_Z_INDEX = 9998
COMPONENT_SPINNER_COLOR = '#d97d5c'
COMPONENT_SPINNER_SIZE = '24px'
COMPONENT_SPINNER_THICKNESS = '3px'
COMPONENT_TITLE_BAR_BACKDROP_FILTER = 'blur(4px)'
COMPONENT_TITLE_BAR_BACKGROUND = 'rgba(0,0,0,0.4)'
COMPONENT_TITLE_BAR_BORDER_RADIUS = '20px'
COMPONENT_TITLE_BAR_COLOR = '#ffffff'
COMPONENT_TITLE_BAR_FONT_SIZE = '0.95rem'
COMPONENT_TITLE_BAR_FONT_WEIGHT = 600
COMPONENT_TITLE_BAR_PADDING = '4px 16px'
COMPONENT_TITLE_BAR_POINTER_EVENTS = 'none'
COMPONENT_TITLE_BAR_TEXT_SHADOW = '0 1px 3px rgba(0,0,0,0.7)'
COMPONENT_TITLE_BAR_TOP = '16px'
COMPONENT_TITLE_BAR_Z_INDEX = 9999
COMPONENT_TOAST_BACKDROP_FILTER = 'blur(8px)'
COMPONENT_TOAST_BACKGROUND = 'rgba(0,0,0,0.75)'
COMPONENT_TOAST_BORDER_RADIUS = '8px'
COMPONENT_TOAST_COLOR = '#ffffff'
COMPONENT_TOAST_ERROR_ICON_COLOR = '#d4645c'
COMPONENT_TOAST_FONT_SIZE = '0.85rem'
COMPONENT_TOAST_PADDING = '10px 20px'
COMPONENT_TOAST_SUCCESS_ICON_COLOR = '#4d9e6c'
COMPONENT_TOAST_WARNING_ICON_COLOR = '#d4a33a'
COMPONENT_TOOLTIP_BACKDROP_FILTER = 'blur(8px)'
COMPONENT_TOOLTIP_BACKGROUND = 'rgba(0,0,0,0.85)'
COMPONENT_TOOLTIP_BORDER_RADIUS = '6px'
COMPONENT_TOOLTIP_COLOR = '#ffffff'
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
    'color-functional-glow-orange': COLOR_FUNCTIONAL_GLOW_ORANGE,
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
    'color-brand-primary': '#d97d5c',
    'color-brand-primary-active': '#ae5f43',
    'color-brand-primary-hover': '#c46e4f',
    'color-brand-secondary': '#7ba4cc',
    'color-brand-secondary-active': '#5c84a8',
    'color-brand-secondary-hover': '#6b94ba',
    'color-chart-polarity-negative': '#d9805c',
    'color-chart-polarity-neutral': '#8a8a8a',
    'color-chart-polarity-positive': '#5aab8a',
    'color-chart-polarity-very-negative': '#cc6b6b',
    'color-chart-polarity-very-positive': '#3d8c6e',
    'color-emotion-negative': '#d9805c',
    'color-emotion-neutral': '#c4a855',
    'color-emotion-positive': '#8fbf9f',
    'color-emotion-very-negative': '#cc6b6b',
    'color-emotion-very-positive': '#5aab8a',
    'color-functional-border-light': 'rgba(255,255,255,0.12)',
    'color-functional-border-medium': 'rgba(255,255,255,0.15)',
    'color-functional-border-strong': 'rgba(255,255,255,0.25)',
    'color-functional-disabled': '#737373',
    'color-functional-disabled-bg': 'rgba(115,115,115,0.25)',
    'color-functional-glow-orange': 'rgba(217,125,92,0.35)',
    'color-functional-link': '#7ba4cc',
    'color-functional-overlay-dark': 'rgba(0,0,0,0.55)',
    'color-functional-overlay-light': 'rgba(0,0,0,0.40)',
    'color-functional-overlay-medium': 'rgba(0,0,0,0.45)',
    'color-functional-selected': '#d97d5c',
    'color-functional-text-on-dark': '#ffffff',
    'color-functional-text-secondary': '#cccccc',
    'color-functional-text-tertiary': '#aaaaaa',
    'color-gradient-hotcold0': '#b8d4e3',
    'color-gradient-hotcold1': '#e8e0b0',
    'color-gradient-hotcold2': '#d9ac7c',
    'color-gradient-hotcold3': '#d9886b',
    'color-gradient-hotcold4': '#b85c4a',
    'color-gradient-neg0': '#252525',
    'color-gradient-neg1': '#636363',
    'color-gradient-neg2': '#bdbdbd',
    'color-gradient-neg3': '#f0f0f0',
    'color-gradient-neg4': '#f0edc5',
    'color-gradient-pos0': '#004529',
    'color-gradient-pos1': '#3d8c5e',
    'color-gradient-pos2': '#5aab8a',
    'color-gradient-pos3': '#a3d4b5',
    'color-gradient-pos4': '#f0edc5',
    'color-neutral-0': '#ffffff',
    'color-neutral-100': '#f5f5f5',
    'color-neutral-200': '#e5e5e5',
    'color-neutral-300': '#d4d4d4',
    'color-neutral-400': '#a3a3a3',
    'color-neutral-50': '#fafafa',
    'color-neutral-500': '#737373',
    'color-neutral-600': '#525252',
    'color-neutral-700': '#404040',
    'color-neutral-800': '#262626',
    'color-neutral-900': '#1a1a1a',
    'color-semantic-error': '#d4645c',
    'color-semantic-info': '#7ba4cc',
    'color-semantic-success': '#4d9e6c',
    'color-semantic-warning': '#d4a33a',
    'component-badge-border-radius': '12px',
    'component-badge-font-size': '0.65rem',
    'component-badge-font-weight': 600,
    'component-badge-padding': '2px 8px',
    'component-badge-text-transform': 'uppercase',
    'component-boundary-color': '#d97d5c',
    'component-boundary-dash-array': '6 3',
    'component-boundary-fill-opacity': 0.08,
    'component-boundary-weight': 2,
    'component-chart-axis-color': 'rgba(255,255,255,0.3)',
    'component-chart-bar-color': '#7ba4cc',
    'component-chart-grid-color': 'rgba(255,255,255,0.1)',
    'component-chart-height': 300,
    'component-chart-label-color': '#aaaaaa',
    'component-data-overlay-backdrop-filter': 'blur(8px)',
    'component-data-overlay-background': 'rgba(0,0,0,0.45)',
    'component-data-overlay-border': '1px solid rgba(255,255,255,0.10)',
    'component-data-overlay-border-radius': '8px',
    'component-data-overlay-color': '#ffffff',
    'component-data-overlay-font-size': '0.78rem',
    'component-data-overlay-left': '14px',
    'component-data-overlay-line-height': 1.5,
    'component-data-overlay-padding': '5px 14px',
    'component-data-overlay-pointer-events': 'none',
    'component-data-overlay-top': '54px',
    'component-data-overlay-z-index': 9999,
    'component-data-table-border-color': 'rgba(255,255,255,0.08)',
    'component-data-table-cell-padding': '6px 12px',
    'component-data-table-font-size': '0.8rem',
    'component-data-table-header-background': 'rgba(0,0,0,0.3)',
    'component-data-table-header-color': '#ffffff',
    'component-data-table-header-font-weight': 600,
    'component-data-table-row-hover-background': 'rgba(217,125,92,0.08)',
    'component-dialog-backdrop-filter': 'blur(12px)',
    'component-dialog-background': 'rgba(0,0,0,0.55)',
    'component-dialog-border': '1px solid rgba(255,255,255,0.12)',
    'component-dialog-border-radius': '12px',
    'component-dialog-color': '#ffffff',
    'component-dialog-divider-color': '#404040',
    'component-dialog-font-size': '1rem',
    'component-dialog-large-max-width': '800px',
    'component-dialog-max-width': '600px',
    'component-dialog-padding': '20px 32px',
    'component-dialog-small-max-width': '400px',
    'component-dialog-title-font-size': '1.25rem',
    'component-dialog-title-font-weight': 600,
    'component-emotion-dot-inner-opacity': 0.92,
    'component-emotion-dot-inner-radius': 7,
    'component-emotion-dot-inner-stroke-color': '#ffffff',
    'component-emotion-dot-inner-stroke-width': 2,
    'component-emotion-dot-outer-opacity': 0.12,
    'component-emotion-dot-outer-radius': 13,
    'component-hud-button-backdrop-filter': 'blur(8px)',
    'component-hud-button-background': 'rgba(30,30,30,0.75)',
    'component-hud-button-border': '1px solid rgba(255,255,255,0.15)',
    'component-hud-button-border-radius': '10px',
    'component-hud-button-color': '#ffffff',
    'component-hud-button-disabled-cursor': 'not-allowed',
    'component-hud-button-disabled-opacity': 0.4,
    'component-hud-button-font-size': '1.1rem',
    'component-hud-button-height': '44px',
    'component-hud-button-hover-background': 'rgba(217,125,92,0.25)',
    'component-hud-button-transition': 'background 0.2s',
    'component-hud-button-width': '44px',
    'component-hud-button-z-index': 9999,
    'component-legend-backdrop-filter': 'blur(4px)',
    'component-legend-background': 'rgba(0,0,0,0.6)',
    'component-legend-border-radius': '8px',
    'component-legend-bottom': '12px',
    'component-legend-color': '#ffffff',
    'component-legend-font-size': '0.75rem',
    'component-legend-gradient-bar-height': '10px',
    'component-legend-gradient-bar-width': '120px',
    'component-legend-label-color': '#aaaaaa',
    'component-legend-label-font-size': '0.7rem',
    'component-legend-line-height': 1.6,
    'component-legend-padding': '10px 14px',
    'component-legend-pointer-events': 'none',
    'component-legend-right': '12px',
    'component-legend-title-font-size': '0.85rem',
    'component-legend-title-font-weight': 700,
    'component-legend-z-index': 9998,
    'component-spinner-color': '#d97d5c',
    'component-spinner-size': '24px',
    'component-spinner-thickness': '3px',
    'component-title-bar-backdrop-filter': 'blur(4px)',
    'component-title-bar-background': 'rgba(0,0,0,0.4)',
    'component-title-bar-border-radius': '20px',
    'component-title-bar-color': '#ffffff',
    'component-title-bar-font-size': '0.95rem',
    'component-title-bar-font-weight': 600,
    'component-title-bar-padding': '4px 16px',
    'component-title-bar-pointer-events': 'none',
    'component-title-bar-text-shadow': '0 1px 3px rgba(0,0,0,0.7)',
    'component-title-bar-top': '16px',
    'component-title-bar-z-index': 9999,
    'component-toast-backdrop-filter': 'blur(8px)',
    'component-toast-background': 'rgba(0,0,0,0.75)',
    'component-toast-border-radius': '8px',
    'component-toast-color': '#ffffff',
    'component-toast-error-icon-color': '#d4645c',
    'component-toast-font-size': '0.85rem',
    'component-toast-padding': '10px 20px',
    'component-toast-success-icon-color': '#4d9e6c',
    'component-toast-warning-icon-color': '#d4a33a',
    'component-tooltip-backdrop-filter': 'blur(8px)',
    'component-tooltip-background': 'rgba(0,0,0,0.85)',
    'component-tooltip-border-radius': '6px',
    'component-tooltip-color': '#ffffff',
    'component-tooltip-font-size': '0.75rem',
    'component-tooltip-max-width': '300px',
    'component-tooltip-padding': '6px 10px',
}

LIGHT_TOKENS = {
    'color-brand-primary': '#d97d5c',
    'color-brand-primary-active': '#ae5f43',
    'color-brand-primary-hover': '#c46e4f',
    'color-brand-secondary': '#7ba4cc',
    'color-brand-secondary-active': '#5c84a8',
    'color-brand-secondary-hover': '#6b94ba',
    'color-chart-polarity-negative': '#cc7248',
    'color-chart-polarity-neutral': '#8a8a8a',
    'color-chart-polarity-positive': '#4a9b78',
    'color-chart-polarity-very-negative': '#bd5c5c',
    'color-chart-polarity-very-positive': '#357a5c',
    'color-emotion-negative': '#cc7248',
    'color-emotion-neutral': '#b89a45',
    'color-emotion-positive': '#7aad8a',
    'color-emotion-very-negative': '#bd5c5c',
    'color-emotion-very-positive': '#4a9b78',
    'color-functional-border-light': 'rgba(0,0,0,0.08)',
    'color-functional-border-medium': 'rgba(0,0,0,0.12)',
    'color-functional-border-strong': 'rgba(0,0,0,0.18)',
    'color-functional-disabled': '#a3a3a3',
    'color-functional-disabled-bg': 'rgba(115,115,115,0.15)',
    'color-functional-glow-orange': 'rgba(217,125,92,0.2)',
    'color-functional-link': '#6b94c4',
    'color-functional-overlay-dark': 'rgba(255,255,255,0.88)',
    'color-functional-overlay-light': 'rgba(255,255,255,0.65)',
    'color-functional-overlay-medium': 'rgba(255,255,255,0.78)',
    'color-functional-selected': '#d97d5c',
    'color-functional-text-on-dark': '#1a1a1a',
    'color-functional-text-secondary': '#525252',
    'color-functional-text-tertiary': '#737373',
    'color-gradient-hotcold0': '#c4dce8',
    'color-gradient-hotcold1': '#ece4b8',
    'color-gradient-hotcold2': '#d9ac7c',
    'color-gradient-hotcold3': '#d9886b',
    'color-gradient-hotcold4': '#b85c4a',
    'color-gradient-neg0': '#252525',
    'color-gradient-neg1': '#636363',
    'color-gradient-neg2': '#bdbdbd',
    'color-gradient-neg3': '#f0f0f0',
    'color-gradient-neg4': '#f0edc5',
    'color-gradient-pos0': '#004529',
    'color-gradient-pos1': '#3d8c5e',
    'color-gradient-pos2': '#5aab8a',
    'color-gradient-pos3': '#a3d4b5',
    'color-gradient-pos4': '#f0edc5',
    'color-neutral-0': '#ffffff',
    'color-neutral-100': '#f5f5f5',
    'color-neutral-200': '#e5e5e5',
    'color-neutral-300': '#d4d4d4',
    'color-neutral-400': '#a3a3a3',
    'color-neutral-50': '#fafafa',
    'color-neutral-500': '#737373',
    'color-neutral-600': '#525252',
    'color-neutral-700': '#404040',
    'color-neutral-800': '#262626',
    'color-neutral-900': '#1a1a1a',
    'color-semantic-error': '#c4554d',
    'color-semantic-info': '#6b94c4',
    'color-semantic-success': '#3d8c5e',
    'color-semantic-warning': '#c49430',
    'component-badge-border-radius': '12px',
    'component-badge-font-size': '0.65rem',
    'component-badge-font-weight': 600,
    'component-badge-padding': '2px 8px',
    'component-badge-text-transform': 'uppercase',
    'component-boundary-color': '#d97d5c',
    'component-boundary-dash-array': '6 3',
    'component-boundary-fill-opacity': 0.08,
    'component-boundary-weight': 2,
    'component-chart-axis-color': 'rgba(0,0,0,0.15)',
    'component-chart-bar-color': '#7ba4cc',
    'component-chart-grid-color': 'rgba(0,0,0,0.06)',
    'component-chart-height': 300,
    'component-chart-label-color': '#737373',
    'component-data-overlay-backdrop-filter': 'blur(8px)',
    'component-data-overlay-background': 'rgba(255,255,255,0.85)',
    'component-data-overlay-border': '1px solid rgba(0,0,0,0.06)',
    'component-data-overlay-border-radius': '8px',
    'component-data-overlay-color': '#1a1a1a',
    'component-data-overlay-font-size': '0.78rem',
    'component-data-overlay-left': '14px',
    'component-data-overlay-line-height': 1.5,
    'component-data-overlay-padding': '5px 14px',
    'component-data-overlay-pointer-events': 'none',
    'component-data-overlay-top': '54px',
    'component-data-overlay-z-index': 9999,
    'component-data-table-border-color': 'rgba(0,0,0,0.06)',
    'component-data-table-cell-padding': '6px 12px',
    'component-data-table-font-size': '0.8rem',
    'component-data-table-header-background': 'rgba(0,0,0,0.04)',
    'component-data-table-header-color': '#1a1a1a',
    'component-data-table-header-font-weight': 600,
    'component-data-table-row-hover-background': 'rgba(217,125,92,0.06)',
    'component-dialog-backdrop-filter': 'blur(12px)',
    'component-dialog-background': 'rgba(255,255,255,0.92)',
    'component-dialog-border': '1px solid rgba(0,0,0,0.08)',
    'component-dialog-border-radius': '12px',
    'component-dialog-color': '#1a1a1a',
    'component-dialog-divider-color': '#e5e5e5',
    'component-dialog-font-size': '1rem',
    'component-dialog-large-max-width': '800px',
    'component-dialog-max-width': '600px',
    'component-dialog-padding': '20px 32px',
    'component-dialog-small-max-width': '400px',
    'component-dialog-title-font-size': '1.25rem',
    'component-dialog-title-font-weight': 600,
    'component-emotion-dot-inner-opacity': 0.92,
    'component-emotion-dot-inner-radius': 7,
    'component-emotion-dot-inner-stroke-color': '#ffffff',
    'component-emotion-dot-inner-stroke-width': 2,
    'component-emotion-dot-outer-opacity': 0.18,
    'component-emotion-dot-outer-radius': 13,
    'component-hud-button-backdrop-filter': 'blur(8px)',
    'component-hud-button-background': 'rgba(255,255,255,0.85)',
    'component-hud-button-border': '1px solid rgba(0,0,0,0.1)',
    'component-hud-button-border-radius': '10px',
    'component-hud-button-color': '#1a1a1a',
    'component-hud-button-disabled-cursor': 'not-allowed',
    'component-hud-button-disabled-opacity': 0.35,
    'component-hud-button-font-size': '1.1rem',
    'component-hud-button-height': '44px',
    'component-hud-button-hover-background': 'rgba(217,125,92,0.12)',
    'component-hud-button-transition': 'background 0.2s',
    'component-hud-button-width': '44px',
    'component-hud-button-z-index': 9999,
    'component-legend-backdrop-filter': 'blur(4px)',
    'component-legend-background': 'rgba(255,255,255,0.85)',
    'component-legend-border-radius': '8px',
    'component-legend-bottom': '12px',
    'component-legend-color': '#1a1a1a',
    'component-legend-font-size': '0.75rem',
    'component-legend-gradient-bar-height': '10px',
    'component-legend-gradient-bar-width': '120px',
    'component-legend-label-color': '#737373',
    'component-legend-label-font-size': '0.7rem',
    'component-legend-line-height': 1.6,
    'component-legend-padding': '10px 14px',
    'component-legend-pointer-events': 'none',
    'component-legend-right': '12px',
    'component-legend-title-font-size': '0.85rem',
    'component-legend-title-font-weight': 700,
    'component-legend-z-index': 9998,
    'component-spinner-color': '#d97d5c',
    'component-spinner-size': '24px',
    'component-spinner-thickness': '3px',
    'component-title-bar-backdrop-filter': 'blur(4px)',
    'component-title-bar-background': 'rgba(255,255,255,0.75)',
    'component-title-bar-border-radius': '20px',
    'component-title-bar-color': '#1a1a1a',
    'component-title-bar-font-size': '0.95rem',
    'component-title-bar-font-weight': 600,
    'component-title-bar-padding': '4px 16px',
    'component-title-bar-pointer-events': 'none',
    'component-title-bar-text-shadow': 'none',
    'component-title-bar-top': '16px',
    'component-title-bar-z-index': 9999,
    'component-toast-backdrop-filter': 'blur(8px)',
    'component-toast-background': 'rgba(255,255,255,0.92)',
    'component-toast-border-radius': '8px',
    'component-toast-color': '#1a1a1a',
    'component-toast-error-icon-color': '#c4554d',
    'component-toast-font-size': '0.85rem',
    'component-toast-padding': '10px 20px',
    'component-toast-success-icon-color': '#3d8c5e',
    'component-toast-warning-icon-color': '#c49430',
    'component-tooltip-backdrop-filter': 'blur(8px)',
    'component-tooltip-background': 'rgba(255,255,255,0.95)',
    'component-tooltip-border-radius': '6px',
    'component-tooltip-color': '#1a1a1a',
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
