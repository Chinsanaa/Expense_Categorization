"""
Short official English display names for merchants (charts & tables).
Falls back to the original name when no mapping exists.
"""
import math

# Exact merchant string -> display name
EXACT_NAMES: dict[str, str] = {
    "上海纽约大学": "NYU Shanghai",
    "美团": "Meituan",
    "美团平台商户": "Meituan",
    "滴滴出行": "DiDi",
    "得物-得到美好事物": "Poizon",
    "得物APP平台商户": "Poizon",
    "荟选集市后滩店": "Huixuan Market",
    "上海一网通办缴费平台": "Shanghai Gov Pay",
    "淘宝平台商户": "Taobao",
    "淘宝闪购": "Taobao Flash",
    "橘柚梧桐": "Juyou Wutong",
    "喜士多": "C-Store",
    "喜士多(高青西店)": "C-Store",
    "喜士多（济明门市）": "C-Store",
    "喝清喝理（上海）餐饮管理有限公司": "INS",
    "上海国际旅行卫生保健中心": "Travel Health Center",
    "高德打车": "Amap",
    "麦当劳": "McDonald's",
    "汉堡王(上海地产城方耀华)": "Burger King",
    "全家": "FamilyMart",
    "萨莉亚": "Saizeriya",
    "萨莉亚南京东路四店": "Saizeriya",
    "无印良品MUJI": "MUJI",
    "春秋航空": "Spring Airlines",
    "卯时六点半": "Maoshi",
    "上海饱猫餐饮管理有限公司": "Baomao Catering",
    "上海蕤盛工贸": "Ruisheng Trading",
    "上海谱墨品牌管理有限公司": "Pumo Brands",
    "上海地铁": "Shanghai Metro",
    "上海申通地铁资产经营管理有限公司": "Shanghai Metro",
    "哈啰出行": "HelloBike",
    "拼多多": "Pinduoduo",
    "拼多多平台商户": "Pinduoduo",
    "喜茶": "HEYTEA",
    "霸王茶姬": "CHAGEE",
    "蜜雪冰城": "Mixue",
    "蜜雪冰城934055店": "Mixue",
    "达美乐": "Domino's",
    "必胜客": "Pizza Hut",
    "名创优品": "MINISO",
    "大黄鹅": "Big Yellow Goose",
    "大象智贩": "Elephant Vending",
    "友宝昂莱": "Ubox Vending",
    "荣康倍儿爽共享按摩椅": "Rongkang Massage",
    "上海市豹喵酒吧": "Baomao Bar",
    "卓联（上海）餐饮服务有限公司": "Zhuolian Catering",
    "昆仑唐府兰州牛肉面（后滩店）": "Kunlun Tangfu Noodles",
    "昆仑唐府兰州纯汤牛肉面": "Kunlun Tangfu Noodles",
    "济明路蘭州牛肉面（百热客）": "Lanzhou Beef Noodles",
    "马永胜牛肉面": "Ma Yongsheng Noodles",
    "蘇小柳": "Su Xiaoliu",
    "美淑家·韩国料理·石锅拌饭": "Meishujia Bibimbap",
    "饿梨酱Hey Guac·美洲活力西餐": "HeyGuac",
    "正三熙by韩国街小木屋烤肉": "Zheng San Xi BBQ",
    "鹈鹕镇大王": "Pelican King",
    "浦东机场": "Pudong Airport",
    "淘天物流科技有限公司": "Taotian Logistics",
    "中国移动": "China Mobile",
    "中石化上海": "Sinopec",
    "上海公共交通卡股份有限公司": "Shanghai Transit Card",
    "宁波市轨道交通集团有限公司线网调度分公司": "Ningbo Metro",
    "乐科智控": "Leke Vending",
    "好德": "Alldays",
    "统一超商(上海)便利有限公司": "7-ELEVEN",
    "沪浙7-ELEVEN": "7-ELEVEN",
    "7-11浙江宁波": "7-ELEVEN",
    "7-ELEVEN上海(嘉里)": "7-ELEVEN",
    "杂物社": "ZAKKA MART",
    "初易（上海）餐饮管理有限公司": "Chuyi Catering",
    "上海檀檀之家餐饮管理有限公司": "Tantan Catering",
    "上海芸译餐饮有限公司": "Yunyi Catering",
    "上海英和企业管理有限公司": "Yinghe Enterprise",
    "上海香雪海国际贸易有限公司": "Xiangxuehai Trading",
    "上海优悠生活商业管理有限公司": "Youyou Life",
    "上海都畅数字技术有限公司": "Duchang Digital",
    "叶浦都餐饮管理（上海）有限公司": "Yepudu Catering",
    "昔客堡（上海）餐饮服务有限公司": "Xikebao Catering",
    "久鼎餐饮管理": "Jiuding Catering",
    "杜福睿(上海)商业有限公司": "Dufurui Commerce",
    "云上智造（上海）科技发展有限公司": "Yunshang Tech",
    "雅纳晟嘉影文化传播（杭州）有限公司": "Yanasheng Media",
    "广州市玩客游乐设备有限公司": "Wanke Amusement",
    "广州大头贴": "Guangzhou Photo Booth",
    "宁波市鄞州首南芳霞饭店": "Shounan Fangxia",
    "个人收款尼彦兵": "Personal (Niyanbing)",
    "高青西门市": "Gaoqing Store",
    "奥乐齐商业（": "ALDI",
    "聆动": "Lingdong",
    "聆动电子科技": "Lingdong Tech",
    "小满手工粉": "Xiaoman Noodles",
    "JUNGLEplus广州动漫新城店": "JUNGLEplus",
    "YogurtDay酸奶（世博天地店）": "YogurtDay",
    "🔥战🙏狼🔥": "War Wolf",
    "ao**店": "Online Store",
    "wa**店": "Online Store",
    "ws**1": "Online Store",
    "恒品**店": "Online Store",
    "绿联**店": "Online Store",
    # Already English — normalize to short official forms
    "13DE MARZO CAFÉ": "13DE MARZO",
    "luckin coffee": "Luckin Coffee",
    "SUBWAY": "Subway",
    "POPEYES": "Popeyes",
    "APIO艾彼悠": "APIO",
    "Holy Bagel": "Holy Bagel",
    "Habibi": "Habibi",
    "AMINO AMIGO": "Amino Amigo",
    "LA BARAKA UV": "La Baraka",
    "LAWSON": "Lawson",
    "K-MART": "K-Mart",
    "KKV": "KKV",
    "ODAY": "O'Day",
    "Evie": "Evie",
    "floating kitchen": "Floating Kitchen",
}

# Substring rules (more specific patterns should appear first)
SUBSTRING_RULES: list[tuple[str, str]] = [
    ("上海纽约大学", "NYU Shanghai"),
    ("纽约大学", "NYU Shanghai"),
    ("一网通办", "Shanghai Gov Pay"),
    ("国际旅行卫生保健", "Travel Health Center"),
    ("荟选集市", "Huixuan Market"),
    ("得物", "Poizon"),
    ("淘宝闪购", "Taobao Flash"),
    ("淘宝", "Taobao"),
    ("美团", "Meituan"),
    ("滴滴", "DiDi"),
    ("高德", "Amap"),
    ("哈啰", "HelloBike"),
    ("喜士多", "C-Store"),
    ("无印良品", "MUJI"),
    ("蜜雪冰城", "Mixue"),
    ("汉堡王", "Burger King"),
    ("萨莉亚", "Saizeriya"),
    ("麦当劳", "McDonald's"),
    ("全家", "FamilyMart"),
    ("7-ELEVEN", "7-ELEVEN"),
    ("7-11", "7-ELEVEN"),
    ("拼多多", "Pinduoduo"),
    ("名创优品", "MINISO"),
    ("春秋航空", "Spring Airlines"),
    ("浦东机场", "Pudong Airport"),
    ("申通地铁", "Shanghai Metro"),
    ("上海地铁", "Shanghai Metro"),
    ("轨道交通", "Metro"),
    ("昆仑唐府", "Kunlun Tangfu Noodles"),
    ("蘭州牛肉面", "Lanzhou Beef Noodles"),
    ("牛肉面", "Beef Noodles"),
    ("奥乐齐", "ALDI"),
    ("中石化", "Sinopec"),
    ("中国移动", "China Mobile"),
]


def display_merchant(name: str) -> str:
    """Return a short English display name for a merchant."""
    if name is None:
        return ""
    if isinstance(name, float) and math.isnan(name):
        return ""
    text = str(name).strip()
    if not text:
        return text

    if text in EXACT_NAMES:
        return EXACT_NAMES[text]

    for pattern, label in SUBSTRING_RULES:
        if pattern in text:
            return label

    # Mostly ASCII — return as-is (already English)
    try:
        text.encode("ascii")
        return text
    except UnicodeEncodeError:
        pass

    return text


def add_display_names(df, source_col: str = "merchant", target_col: str = "merchant_display"):
    """Add a display-name column to a DataFrame copy."""
    out = df.copy()
    out[target_col] = out[source_col].map(display_merchant)
    return out


def aggregate_merchants(df, n: int = 12) -> "pd.DataFrame":
    """Sum spending by English display name (merges e.g. two Poizon entries)."""
    import pandas as pd

    return (
        df.assign(merchant_display=df['merchant'].map(display_merchant))
        .groupby('merchant_display', as_index=False)['amount']
        .sum()
        .nlargest(n, 'amount')
    )
