"""高考择校数据（中国教育在线 eol.cn API，免 Key）。

实测 api.eol.cn 可达，返回结构化院校数据。
- search_schools: 按关键词或城市搜院校
- list_city_schools: 按城市 code 列院校（含 211/985/类型）
分数线端点不稳定，暂以院校基础信息为主（已足够支撑择校建议）。
"""
from __future__ import annotations

import httpx

from app.tools.base import Doc, safe

# 主要城市 -> city_id（eol.cn 编码）
CITY_IDS = {
    "北京": "11", "上海": "31", "西安": "6101", "南京": "3201",
    "武汉": "4201", "成都": "5101", "广州": "4401", "杭州": "3301",
    "天津": "12", "重庆": "50", "长沙": "4301", "青岛": "3702",
}
# 省份 -> province_id
PROVINCE_IDS = {
    "陕西": "61", "北京": "11", "上海": "31", "江苏": "32", "广东": "44",
    "山东": "37", "四川": "51", "湖北": "42", "浙江": "33", "河南": "41",
}

_API = "https://api.eol.cn/gkcx/api/"
_HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/124.0"}


def _resolve_city_id(query: str) -> str | None:
    """从 query 里识别城市。"""
    for city, cid in CITY_IDS.items():
        if city in query:
            return cid
    return None


@safe("gaokao_schools")
def search(query: str, max_results: int = 12) -> list[Doc]:
    """按关键词或城市搜院校。

    query 含城市名(如"西安")时按城市列；否则按关键词搜。
    返回院校基础信息：名称/类型/层次/211/985/办学性质。
    """
    city_id = _resolve_city_id(query)
    params: dict = {"page": 1, "size": max_results, "uri": "apidata/api/gk/school/lists"}
    if city_id:
        params["city_id"] = city_id
    else:
        params["keyword"] = query

    r = httpx.get(_API, params=params, headers=_HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json().get("data", {})
    items = data.get("item", []) if isinstance(data, dict) else []

    docs: list[Doc] = []
    for s in items[:max_results]:
        tags = []
        if s.get("f985") == "1":
            tags.append("985")
        if s.get("f211") == "1":
            tags.append("211")
        content = (
            f"院校：{s.get('name','')}  类型：{s.get('type_name','')}  "
            f"层次：{s.get('level_name','')}  办学：{s.get('nature_name','')}  "
            f"属地：{s.get('province_name','')}{s.get('city_name','')}  "
            f"标签：{' '.join(tags) or '普通本科'}  "
            f"代码：{s.get('code_enroll','')}"
        )
        docs.append(
            Doc(
                source="gaokao_schools",
                title=s.get("name", ""),
                url=f"https://gkcx.eol.cn/school/{s.get('school_id')}",
                content=content,
                meta={"city": s.get("city_name"), "tags": tags, "type": s.get("type_name")},
            )
        )
    return docs
