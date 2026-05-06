import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAMESPACES = {"eu-gdpr", "kr-pipa", "us-ca"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_unified_source_registry_lists_all_namespaces():
    registry = read_json(ROOT / "index" / "unified-source-registry.json")

    assert registry["count"] == 3
    assert {source["namespace"] for source in registry["sources"]} == NAMESPACES


def test_unified_authority_index_is_namespaced_and_nonempty():
    authority_index = read_json(ROOT / "index" / "unified-authority-index.json")

    assert authority_index["count"] > 2_000
    assert set(authority_index["by_namespace"]) == NAMESPACES
    assert all(count > 0 for count in authority_index["by_namespace"].values())
    assert authority_index["by_namespace"]["us-ca"] >= 231
    assert authority_index["duplicate_original_ids"] == {}
    assert all(
        authority["unified_id"].startswith(f"{authority['namespace']}:")
        for authority in authority_index["authorities"]
    )


def test_unified_california_authorities_are_grounded():
    authority_index = read_json(ROOT / "index" / "unified-authority-index.json")

    for authority in authority_index["authorities"]:
        if authority["namespace"] != "us-ca":
            continue
        assert authority["path"], authority["unified_id"]
        assert (ROOT / authority["path"]).exists(), authority["unified_id"]
        assert authority["official_url"].startswith("http"), authority["unified_id"]
        assert (ROOT / authority["source_index"]).exists(), authority["unified_id"]


def test_unified_topic_authority_refs_resolve():
    authority_index = read_json(ROOT / "index" / "unified-authority-index.json")
    topic_index = read_json(ROOT / "index" / "unified-topic-index.json")
    authority_ids = {authority["unified_id"] for authority in authority_index["authorities"]}

    for topic in topic_index["topics"]:
        for authority_ref in topic["authority_refs"]:
            assert authority_ref in authority_ids, (topic["unified_id"], authority_ref)


def test_jurisdiction_routing_points_to_imported_kbs():
    routing = read_json(ROOT / "index" / "jurisdiction-routing.json")

    assert {route["namespace"] for route in routing["routes"]} == NAMESPACES
    for route in routing["routes"]:
        assert (ROOT / route["library_root"]).exists()
        assert (ROOT / route["index_root"]).exists()
        assert (ROOT / route["source_registry"]).exists()


def test_import_manifests_exist_and_exclude_inbox_dirs():
    for namespace in NAMESPACES:
        manifest = read_json(ROOT / "kb" / namespace / "manifest.json")
        assert manifest["namespace"] == namespace
        assert manifest["file_counts"]["library"] > 0
        assert not (ROOT / "kb" / namespace / "library" / "inbox").exists()
