#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字排盘工具
基于 lunar_python 库，提供完整的八字排盘、大运流年、小运计算功能。

用法：
    python3 bazi_calculator.py --year 1990 --month 5 --day 20 --hour 14 --minute 30 --gender 男 --city 北京
    python3 bazi_calculator.py --json '{"year":1990,"month":5,"day":20,"hour":14,"minute":30,"gender":"男","city":"北京"}'
"""

import argparse
import json
import sys
import math
from datetime import datetime, timedelta

from lunar_python import Solar, Lunar, EightChar

# 六十甲子表
JIAZI_60 = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳",
    "庚午", "辛未", "壬申", "癸酉", "甲戌", "乙亥",
    "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳",
    "壬午", "癸未", "甲申", "乙酉", "丙戌", "丁亥",
    "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥",
    "庚子", "辛丑", "壬寅", "癸卯", "甲辰", "乙巳",
    "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥",
    "壬子", "癸丑", "甲寅", "乙卯", "丙辰", "丁巳",
    "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥",
]

# 城市经度表（用于真太阳时校正）
CITY_LONGITUDE = {
    "北京": 116.40, "上海": 121.47, "广州": 113.26, "深圳": 114.06,
    "成都": 104.07, "重庆": 106.55, "杭州": 120.15, "南京": 118.78,
    "武汉": 114.31, "西安": 108.94, "长沙": 112.94, "郑州": 113.65,
    "天津": 117.20, "青岛": 120.38, "大连": 121.62, "厦门": 118.08,
    "福州": 119.30, "昆明": 102.71, "贵阳": 106.71, "南宁": 108.33,
    "海口": 110.35, "拉萨": 91.14, "西宁": 101.78, "兰州": 103.83,
    "银川": 106.27, "乌鲁木齐": 87.62, "呼和浩特": 111.67, "哈尔滨": 126.63,
    "长春": 125.32, "沈阳": 123.43, "济南": 117.00, "太原": 112.55,
    "石家庄": 114.48, "合肥": 117.27, "南昌": 115.86, "温州": 120.65,
    "宁波": 121.55, "苏州": 120.62, "无锡": 120.30, "东莞": 113.75,
    "佛山": 113.12, "中山": 113.38, "珠海": 113.57, "惠州": 114.41,
    "香港": 114.17, "澳门": 113.55, "台北": 121.57,
}

# 中国大陆夏令时。出生证明/户口登记通常记录当时钟表时间，排盘前需先还原为标准北京时间。
# timeanddate.com 逐年记录：1986-1991 年大陆实行夏令时，香港、澳门不采用本表。
CHINA_DST_PERIODS = {
    1986: ((5, 4, 2, 0), (9, 14, 2, 0)),
    1987: ((4, 12, 2, 0), (9, 13, 2, 0)),
    1988: ((4, 17, 2, 0), (9, 11, 2, 0)),
    1989: ((4, 16, 2, 0), (9, 17, 2, 0)),
    1990: ((4, 15, 2, 0), (9, 16, 2, 0)),
    1991: ((4, 14, 2, 0), (9, 15, 2, 0)),
}

# 五行对应
WUXING_MAP = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
    "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金",
    "戌": "土", "亥": "水",
}

# 阴阳对应
YINYANG_MAP = {
    "甲": "阳", "乙": "阴", "丙": "阳", "丁": "阴", "戊": "阳",
    "己": "阴", "庚": "阳", "辛": "阴", "壬": "阳", "癸": "阴",
    "子": "阳", "丑": "阴", "寅": "阳", "卯": "阴", "辰": "阳",
    "巳": "阴", "午": "阳", "未": "阴", "申": "阳", "酉": "阴",
    "戌": "阳", "亥": "阴",
}

# 十神速查
SHISHEN_MAP = {
    "甲": {"比肩": "甲", "劫财": "乙", "食神": "丙", "伤官": "丁", "正财": "己", "偏财": "戊", "正官": "辛", "七杀": "庚", "正印": "癸", "偏印": "壬"},
    "乙": {"比肩": "乙", "劫财": "甲", "食神": "丁", "伤官": "丙", "正财": "戊", "偏财": "己", "正官": "庚", "七杀": "辛", "正印": "壬", "偏印": "癸"},
    "丙": {"比肩": "丙", "劫财": "丁", "食神": "戊", "伤官": "己", "正财": "辛", "偏财": "庚", "正官": "癸", "七杀": "壬", "正印": "乙", "偏印": "甲"},
    "丁": {"比肩": "丁", "劫财": "丙", "食神": "己", "伤官": "戊", "正财": "庚", "偏财": "辛", "正官": "壬", "七杀": "癸", "正印": "甲", "偏印": "乙"},
    "戊": {"比肩": "戊", "劫财": "己", "食神": "庚", "伤官": "辛", "正财": "癸", "偏财": "壬", "正官": "乙", "七杀": "甲", "正印": "丁", "偏印": "丙"},
    "己": {"比肩": "己", "劫财": "戊", "食神": "辛", "伤官": "庚", "正财": "壬", "偏财": "癸", "正官": "甲", "七杀": "乙", "正印": "丙", "偏印": "丁"},
    "庚": {"比肩": "庚", "劫财": "辛", "食神": "壬", "伤官": "癸", "正财": "乙", "偏财": "甲", "正官": "丁", "七杀": "丙", "正印": "己", "偏印": "戊"},
    "辛": {"比肩": "辛", "劫财": "庚", "食神": "癸", "伤官": "壬", "正财": "甲", "偏财": "乙", "正官": "丙", "七杀": "丁", "正印": "戊", "偏印": "己"},
    "壬": {"比肩": "壬", "劫财": "癸", "食神": "甲", "伤官": "乙", "正财": "丁", "偏财": "丙", "正官": "己", "七杀": "戊", "正印": "辛", "偏印": "庚"},
    "癸": {"比肩": "癸", "劫财": "壬", "食神": "乙", "伤官": "甲", "正财": "丙", "偏财": "丁", "正官": "戊", "七杀": "己", "正印": "庚", "偏印": "辛"},
}


def calc_xiaoyun(shi_zhi: str, gender: str, year_gan: str, count: int = 12) -> list:
    """
    计算小运
    
    小运是从时柱地支开始，按性别顺逆排列。
    - 男命（阳年干）：从时支顺行
    - 女命（阳年干）：从时支逆行
    - 男命（阴年干）：从时支逆行
    - 女命（阴年干）：从时支顺行
    
    Args:
        shi_zhi: 时柱地支
        gender: 性别（男/女）
        year_gan: 年干
        count: 计算几个小运（默认12个，对应流年）
    
    Returns:
        小运干支列表
    """
    # 天干顺序
    tiangan_order = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    # 地支顺序
    dizhi_order = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    
    # 判断年干阴阳
    yang_gan = ["甲", "丙", "戊", "庚", "壬"]
    is_yang_year = year_gan in yang_gan
    
    # 判断顺逆：阳男阴女顺行，阴男阳女逆行
    if (is_yang_year and gender == "男") or (not is_yang_year and gender == "女"):
        shun = True  # 顺行
    else:
        shun = False  # 逆行
    
    # 获取时支在六十甲子中的位置
    # 小运干支从时柱起算：阳男阴女顺行，阴男阳女逆行，逐年推排一干支；独立于大运
    shi_gan_idx = tiangan_order.index(shi_zhi[0]) if len(shi_zhi) == 2 else 0
    shi_zhi_idx = dizhi_order.index(shi_zhi[-1])
    
    xiaoyun_list = []
    gan_idx = shi_gan_idx
    zhi_idx = shi_zhi_idx
    
    for age in range(1, count + 1):
        if shun:
            gan_idx = (gan_idx + 1) % 10
            zhi_idx = (zhi_idx + 1) % 12
        else:
            gan_idx = (gan_idx - 1) % 10
            zhi_idx = (zhi_idx - 1) % 12
        
        xiaoyun_list.append({
            "岁数": age,
            "干支": tiangan_order[gan_idx] + dizhi_order[zhi_idx],
        })
    
    return xiaoyun_list


def is_china_dst(dt: datetime, city: str) -> bool:
    """判断中国大陆 1986-1991 夏令时。香港、澳门不按大陆夏令时处理。"""
    if city in {"香港", "澳门"}:
        return False
    period = CHINA_DST_PERIODS.get(dt.year)
    if not period:
        return False
    start_raw, end_raw = period
    start = datetime(dt.year, *start_raw)
    end = datetime(dt.year, *end_raw)
    return start <= dt < end


def calc_true_solar_datetime(dt: datetime, longitude: float) -> datetime:
    """计算真太阳时。当前使用经度校正；均时差暂不自动加入。"""
    # 北京时间基准经度 120°
    beijing_lon = 120.0
    # 经度差导致的时间差（每度4分钟）
    time_diff = (longitude - beijing_lon) * 4  # 分钟
    # 均时差（粗略估算，实际有季节性变化）
    # 这里简化处理，实际应该用天文算法
    eq_time = 0  # 简化为0，lunar_python 内部已处理节气

    return dt + timedelta(minutes=time_diff)


def calc_true_solar_time(hour: int, minute: int, longitude: float) -> tuple:
    """兼容旧调用：只返回真太阳时的时分，不表达跨日。"""
    dt = calc_true_solar_datetime(datetime(2000, 1, 1, hour, minute), longitude)
    return dt.hour, dt.minute


def bazi_pai_pan(year: int, month: int, day: int, hour: int, minute: int,
                  gender: str = "男", city: str = "北京", use_true_solar: bool = True):
    """八字排盘主函数"""
    result = {}

    # 1. 出生记录时间 -> 夏令时 -> 真太阳时 -> 晚子时换日
    longitude = CITY_LONGITUDE.get(city, 116.40)
    original_dt = datetime(year, month, day, hour, minute)
    dst_applied = is_china_dst(original_dt, city)
    standard_dt = original_dt - timedelta(hours=1) if dst_applied else original_dt

    if use_true_solar:
        true_dt = calc_true_solar_datetime(standard_dt, longitude)
    else:
        true_dt = standard_dt

    chart_dt = true_dt
    zi_hour_next_day = chart_dt.hour == 23
    if zi_hour_next_day:
        # 本 skill 采用“晚子时换日”：23:00-23:59 的日柱按次日排。
        chart_dt = chart_dt + timedelta(days=1)

    adj_year, adj_month, adj_day = chart_dt.year, chart_dt.month, chart_dt.day
    true_hour, true_minute = chart_dt.hour, chart_dt.minute

    result["original_time"] = f"{year}年{month}月{day}日 {hour}:{minute:02d}"
    result["standard_time"] = f"{standard_dt.year}年{standard_dt.month}月{standard_dt.day}日 {standard_dt.hour}:{standard_dt.minute:02d}"
    result["city"] = city
    result["longitude"] = longitude
    result["dst_applied"] = dst_applied
    result["dst_note"] = "已按中国大陆夏令时先减1小时" if dst_applied else None
    result["true_solar_time"] = f"{true_dt.year}年{true_dt.month}月{true_dt.day}日 {true_dt.hour}:{true_dt.minute:02d}" if use_true_solar else None
    result["chart_basis_time"] = f"{adj_year}年{adj_month}月{adj_day}日 {true_hour}:{true_minute:02d}"
    result["zi_hour_next_day"] = zi_hour_next_day
    result["gender"] = gender

    # 2. 排八字
    solar = Solar.fromYmdHms(adj_year, adj_month, adj_day, true_hour, true_minute, 0)
    lunar = solar.getLunar()
    eight = lunar.getEightChar()

    result["solar_date"] = f"{adj_year}-{adj_month:02d}-{adj_day:02d}"
    result["lunar_date"] = lunar.toString()

    # 四柱
    result["pillars"] = {
        "年柱": eight.getYear(),
        "月柱": eight.getMonth(),
        "日柱": eight.getDay(),
        "时柱": eight.getTime(),
    }

    # 天干地支
    result["tiangan"] = {
        "年干": eight.getYearGan(),
        "月干": eight.getMonthGan(),
        "日干": eight.getDayGan(),
        "时干": eight.getTimeGan(),
    }
    result["dizhi"] = {
        "年支": eight.getYearZhi(),
        "月支": eight.getMonthZhi(),
        "日支": eight.getDayZhi(),
        "时支": eight.getTimeZhi(),
    }

    # 藏干
    result["cangan"] = {
        "年支藏干": eight.getYearHideGan(),
        "月支藏干": eight.getMonthHideGan(),
        "日支藏干": eight.getDayHideGan(),
        "时支藏干": eight.getTimeHideGan(),
    }

    # 十神
    result["shishen_gan"] = {
        "年干十神": eight.getYearShiShenGan(),
        "月干十神": eight.getMonthShiShenGan(),
        "时干十神": eight.getTimeShiShenGan(),
    }
    result["shishen_zhi"] = {
        "年支十神": eight.getYearShiShenZhi(),
        "月支十神": eight.getMonthShiShenZhi(),
        "日支十神": eight.getDayShiShenZhi(),
        "时支十神": eight.getTimeShiShenZhi(),
    }

    # 五行
    result["wuxing"] = {
        "年": eight.getYearWuXing(),
        "月": eight.getMonthWuXing(),
        "日": eight.getDayWuXing(),
        "时": eight.getTimeWuXing(),
    }

    # 纳音
    result["nayin"] = {
        "年": eight.getYearNaYin(),
        "月": eight.getMonthNaYin(),
        "日": eight.getDayNaYin(),
        "时": eight.getTimeNaYin(),
    }

    # 空亡
    result["kongwang"] = {
        "年柱空亡": eight.getYearXunKong(),
        "日柱空亡": eight.getDayXunKong(),
    }

    # 胎元命宫身宫
    result["extra"] = {
        "胎元": eight.getTaiYuan(),
        "胎元纳音": eight.getTaiYuanNaYin(),
        "命宫": eight.getMingGong(),
        "命宫纳音": eight.getMingGongNaYin(),
        "身宫": eight.getShenGong(),
        "身宫纳音": eight.getShenGongNaYin(),
        "胎息": eight.getTaiXi(),
        "胎息纳音": eight.getTaiXiNaYin(),
    }

    # 日元
    result["riyuan"] = eight.getDayGan()
    result["riyuan_wuxing"] = WUXING_MAP.get(eight.getDayGan(), "")
    result["riyuan_yinyang"] = YINYANG_MAP.get(eight.getDayGan(), "")

    # 3. 大运
    gender_code = 1 if gender == "男" else 0
    yun = eight.getYun(gender_code)

    year_gan_for_direction = eight.getYearGan()
    is_yang_year = year_gan_for_direction in {"甲", "丙", "戊", "庚", "壬"}
    is_forward = (is_yang_year and gender == "男") or ((not is_yang_year) and gender == "女")

    result["qiyun"] = {
        "起运年龄": f"{yun.getStartYear()}岁{yun.getStartMonth()}个月",
        "起运日期": str(yun.getStartSolar()),
        "顺逆": "顺排" if is_forward else "逆排",
    }

    da_yun = yun.getDaYun()
    da_yun_list = []
    for i, dy in enumerate(da_yun):
        if i == 0:
            continue
        dy_info = {
            "序号": i,
            "干支": dy.getGanZhi(),
            "起岁": dy.getStartYear(),
            "止岁": dy.getEndYear(),
        }
        da_yun_list.append(dy_info)
    result["da_yun"] = da_yun_list

    # 4. 小运（从时柱起算）
    shi_zhi = eight.getTime()
    year_gan = eight.getYearGan()
    result["xiao_yun"] = calc_xiaoyun(shi_zhi, gender, year_gan, 12)

    # 5. 流年（每步大运的流年）
    result["liu_nian"] = []
    for i, dy in enumerate(da_yun):
        if i == 0 or i > 8:
            continue
        liu_nian_list = []
        for ln in dy.getLiuNian():
            liu_nian_list.append({
                "年份": ln.getYear(),
                "干支": ln.getGanZhi(),
            })
        result["liu_nian"].append({
            "大运": dy.getGanZhi(),
            "流年": liu_nian_list,
        })

    # 5. 五行统计
    all_gan = [eight.getYearGan(), eight.getMonthGan(), eight.getDayGan(), eight.getTimeGan()]
    all_zhi = [eight.getYearZhi(), eight.getMonthZhi(), eight.getDayZhi(), eight.getTimeZhi()]
    all_cangan = []
    for cg in [eight.getYearHideGan(), eight.getMonthHideGan(),
               eight.getDayHideGan(), eight.getTimeHideGan()]:
        all_cangan.extend(cg)

    wuxing_count = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
    for g in all_gan:
        wx = WUXING_MAP.get(g, "")
        if wx:
            wuxing_count[wx] += 1
    for z in all_zhi:
        wx = WUXING_MAP.get(z, "")
        if wx:
            wuxing_count[wx] += 1
    for cg in [eight.getYearHideGan(), eight.getMonthHideGan(),
               eight.getDayHideGan(), eight.getTimeHideGan()]:
        if len(cg) == 1:
            weights = [1.0]
        elif len(cg) == 2:
            weights = [0.6, 0.4]
        else:
            weights = [0.6, 0.3, 0.1]
        for c, weight in zip(cg, weights):
            wx = WUXING_MAP.get(c, "")
            if wx:
                wuxing_count[wx] += weight

    result["wuxing_stat"] = wuxing_count

    return result


def format_report(result: dict) -> str:
    """格式化输出报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("八字排盘报告")
    lines.append("=" * 60)
    lines.append("")

    # 基本信息
    lines.append("## 基本信息")
    lines.append(f"出生时间（阳历）: {result['original_time']}")
    lines.append(f"出生地点: {result['city']} (经度 {result['longitude']}°)")
    if result.get("dst_applied"):
        lines.append(f"夏令时校正: {result['dst_note']}，标准北京时间 {result['standard_time']}")
    if result.get("true_solar_time"):
        lines.append(f"真太阳时: {result['true_solar_time']}")
    if result.get("zi_hour_next_day"):
        lines.append(f"子时换日: 23:00-23:59 按次日干支排，排盘基准 {result['chart_basis_time']}")
    else:
        lines.append(f"排盘基准时间: {result['chart_basis_time']}")
    lines.append(f"性别: {result['gender']}")
    lines.append(f"农历: {result['lunar_date']}")
    lines.append("")

    # 四柱
    lines.append("## 四柱排盘")
    lines.append("")
    p = result["pillars"]
    lines.append(f"        年柱      月柱      日柱      时柱")
    lines.append(f"天干:   {result['tiangan']['年干']}        {result['tiangan']['月干']}        {result['tiangan']['日干']}        {result['tiangan']['时干']}")
    lines.append(f"地支:   {result['dizhi']['年支']}        {result['dizhi']['月支']}        {result['dizhi']['日支']}        {result['dizhi']['时支']}")
    lines.append(f"十神:   {result['shishen_gan']['年干十神']}      {result['shishen_gan']['月干十神']}      日元      {result['shishen_gan']['时干十神']}")
    lines.append(f"藏干:   {''.join(result['cangan']['年支藏干']):<8}  {''.join(result['cangan']['月支藏干']):<8}  {''.join(result['cangan']['日支藏干']):<8}  {''.join(result['cangan']['时支藏干']):<8}")
    lines.append(f"纳音:   {result['nayin']['年']:<8}{result['nayin']['月']:<8}{result['nayin']['日']:<8}{result['nayin']['时']:<8}")
    lines.append("")

    lines.append(f"**日元**: {result['riyuan']}（{result['riyuan_wuxing']}，{result['riyuan_yinyang']}）")
    lines.append("")

    # 空亡
    lines.append(f"**空亡**: 年柱{result['kongwang']['年柱空亡']}，日柱{result['kongwang']['日柱空亡']}")
    lines.append("")

    # 胎元命宫
    e = result["extra"]
    lines.append(f"**胎元**: {e['胎元']}（{e['胎元纳音']}）")
    lines.append(f"**命宫**: {e['命宫']}（{e['命宫纳音']}）")
    lines.append(f"**身宫**: {e['身宫']}（{e['身宫纳音']}）")
    lines.append(f"**胎息**: {e['胎息']}（{e['胎息纳音']}）")
    lines.append("")

    # 五行统计
    lines.append("## 五行统计")
    ws = result["wuxing_stat"]
    lines.append(f"金: {ws['金']:.1f}  木: {ws['木']:.1f}  水: {ws['水']:.1f}  火: {ws['火']:.1f}  土: {ws['土']:.1f}")
    missing = [k for k, v in ws.items() if v == 0]
    if missing:
        lines.append(f"**缺五行**: {', '.join(missing)}")
    lines.append("")

    # 大运
    lines.append("## 大运")
    q = result["qiyun"]
    lines.append(f"起运: {q['起运年龄']}，起运日期: {q['起运日期']}")
    lines.append("")
    lines.append(f"{'序号':<4} {'干支':<6} {'起始年':<8} {'止年':<8}")
    lines.append("-" * 32)
    for dy in result["da_yun"]:
        lines.append(f"{dy['序号']:<4} {dy['干支']:<6} {dy['起岁']:<8} {dy['止岁']:<8}")
    lines.append("")

    # 小运
    lines.append("## 小运（童限流年）")
    lines.append("小运从时柱起，阳男阴女顺行，阴男阳女逆行")
    xiaoyun_str = "  ".join([f"{xy['岁数']}岁:{xy['干支']}" for xy in result["xiao_yun"][:6]])
    lines.append(xiaoyun_str)
    xiaoyun_str2 = "  ".join([f"{xy['岁数']}岁:{xy['干支']}" for xy in result["xiao_yun"][6:12]])
    if xiaoyun_str2:
        lines.append(xiaoyun_str2)
    lines.append("")

    # 流年（简略）
    lines.append("## 流年（每步大运）")
    for dy_ln in result["liu_nian"]:
        lines.append(f"\n### 大运 {dy_ln['大运']}")
        for ln in dy_ln["流年"]:
            lines.append(f"  {ln['年份']}年: {ln['干支']}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("排盘完成")
    lines.append("=" * 60)

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="八字排盘工具")
    parser.add_argument("--year", type=int, help="出生年份")
    parser.add_argument("--month", type=int, help="出生月份")
    parser.add_argument("--day", type=int, help="出生日期")
    parser.add_argument("--hour", type=int, default=12, help="出生小时")
    parser.add_argument("--minute", type=int, default=0, help="出生分钟")
    parser.add_argument("--gender", type=str, default="男", choices=["男", "女"], help="性别")
    parser.add_argument("--city", type=str, default="北京", help="出生城市")
    parser.add_argument("--json", type=str, help="JSON格式输入")
    parser.add_argument("--format", type=str, default="text", choices=["text", "json"], help="输出格式")
    args = parser.parse_args()

    if args.json:
        data = json.loads(args.json)
        year = data["year"]
        month = data["month"]
        day = data["day"]
        hour = data.get("hour", 12)
        minute = data.get("minute", 0)
        gender = data.get("gender", "男")
        city = data.get("city", "北京")
    else:
        if not args.year or not args.month or not args.day:
            print("请提供 --year --month --day 参数")
            sys.exit(1)
        year = args.year
        month = args.month
        day = args.day
        hour = args.hour
        minute = args.minute
        gender = args.gender
        city = args.city

    result = bazi_pai_pan(year, month, day, hour, minute, gender, city)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(result))
