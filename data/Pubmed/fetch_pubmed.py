import requests
import json
import time
import os
from xml.etree import ElementTree as ET
from datetime import datetime

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

SEARCH_TERMS = [
    "health misinformation",
    "medical fact check",
    "covid-19 vaccine effectiveness",
    "diabetes mellitus treatment",
    "hypertension management",
    "cancer prevention",
    "antibiotic resistance",
    "mental health treatment",
    "obesity intervention",
    "cardiovascular disease prevention",
    "infectious disease outbreak",
    "nutritional supplement evidence",
    "traditional medicine clinical trial",
    "chronic disease self-management",
    "vaccine safety",
]

# 실행 위치와 무관하게 항상 이 스크립트가 있는 폴더에 저장
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_RESULTS_PER_TERM = 100
BATCH_SIZE = 20


def search_pubmed(query: str, max_results: int = 100) -> list[str]:
    url = BASE_URL + "esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance",
    }
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()["esearchresult"]["idlist"]


def fetch_details(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []

    url = BASE_URL + "efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "xml",
        "retmode": "xml",
    }
    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    articles = []

    for article in root.findall(".//PubmedArticle"):
        try:
            pmid = article.findtext(".//PMID", "")

            title_elem = article.find(".//ArticleTitle")
            title = "".join(title_elem.itertext()) if title_elem is not None else ""

            # Abstract may have multiple labeled sections
            abstract_parts = article.findall(".//AbstractText")
            if len(abstract_parts) == 1:
                abstract = "".join(abstract_parts[0].itertext())
            else:
                abstract = " ".join(
                    "".join(p.itertext()) for p in abstract_parts
                )

            authors = []
            for author in article.findall(".//Author"):
                last = author.findtext("LastName", "")
                fore = author.findtext("ForeName", "")
                if last:
                    authors.append(f"{last} {fore}".strip())

            journal = article.findtext(".//Journal/Title", "")

            pub_date_elem = article.find(".//PubDate")
            pub_date = {}
            if pub_date_elem is not None:
                pub_date = {
                    "year": pub_date_elem.findtext("Year", ""),
                    "month": pub_date_elem.findtext("Month", ""),
                    "day": pub_date_elem.findtext("Day", ""),
                }

            mesh_terms = [
                m.findtext("DescriptorName", "")
                for m in article.findall(".//MeshHeading")
            ]

            keywords = [
                kw.text
                for kw in article.findall(".//Keyword")
                if kw.text
            ]

            articles.append({
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "journal": journal,
                "pub_date": pub_date,
                "mesh_terms": [t for t in mesh_terms if t],
                "keywords": keywords,
            })
        except Exception as e:
            print(f"  [경고] PMID 파싱 실패: {e}")

    return articles


def fetch_all(
    search_terms: list[str] = SEARCH_TERMS,
    max_results_per_term: int = MAX_RESULTS_PER_TERM,
    batch_size: int = BATCH_SIZE,
    output_dir: str = OUTPUT_DIR,
) -> None:
    os.makedirs(output_dir, exist_ok=True)

    all_articles: list[dict] = []
    seen_pmids: set[str] = set()
    term_counts: dict[str, int] = {}

    for term in search_terms:
        print(f"\n[검색] '{term}'")

        try:
            pmids = search_pubmed(term, max_results=max_results_per_term)
        except Exception as e:
            print(f"  검색 실패: {e}")
            continue

        new_pmids = [p for p in pmids if p not in seen_pmids]
        seen_pmids.update(new_pmids)
        print(f"  발견 {len(pmids)}개 / 신규 {len(new_pmids)}개")

        term_articles: list[dict] = []
        total_batches = max(1, (len(new_pmids) + batch_size - 1) // batch_size)

        for i in range(0, len(new_pmids), batch_size):
            batch = new_pmids[i : i + batch_size]
            batch_num = i // batch_size + 1
            print(f"  배치 {batch_num}/{total_batches} 수집 중...")

            try:
                fetched = fetch_details(batch)
                term_articles.extend(fetched)
            except Exception as e:
                print(f"  배치 {batch_num} 실패: {e}")

            time.sleep(0.4)  # NCBI rate limit: 3 req/s without API key

        # Attach search_term tag and collect
        for art in term_articles:
            art["search_term"] = term
        all_articles.extend(term_articles)
        term_counts[term] = len(term_articles)

        # Per-term JSON
        safe = term.replace(" ", "_").replace("/", "-")
        with open(os.path.join(output_dir, f"{safe}.json"), "w", encoding="utf-8") as f:
            json.dump(term_articles, f, ensure_ascii=False, indent=2)

        print(f"  저장 완료: {len(term_articles)}개")
        time.sleep(0.4)

    # Combined output
    metadata = {
        "fetched_at": datetime.now().isoformat(),
        "total_articles": len(all_articles),
        "search_terms": search_terms,
        "articles_per_term": term_counts,
    }

    with open(os.path.join(output_dir, "all_articles.json"), "w", encoding="utf-8") as f:
        json.dump({"metadata": metadata, "articles": all_articles}, f, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\n완료: 총 {len(all_articles)}개 논문 → {output_dir}/")


if __name__ == "__main__":
    fetch_all()
