"""Unit tests for name normalisation and the deterministic/fuzzy Resolver layers (no network)."""
import pytest

from app.resolver.entities import Entity, EntityIndex
from app.resolver.match import resolve
from app.resolver.normalize import has_local_suffix, normalize


def ent(uen, name, status="Live Company", etype="Local Company", formers=()):
    return Entity(uen, name, etype, status, "2020-01-01", "000000", list(formers))


INDEX = EntityIndex([
    ent("U1", "ACME ENGINEERING PTE. LTD."),
    ent("U2", "BETA SOLUTIONS PRIVATE LIMITED", formers=["OLD BETA TRADING PTE LTD"]),
    ent("U3", "TWIN SERVICES PTE LTD"),
    ent("U4", "TWIN SERVICES PTE LTD", status="Struck Off"),
    ent("U5", "GAMMA CONSTRUCTION & ENGINEERING PTE LTD"),
    ent("U6", "DELTA TECH LLP", etype="Limited Liability Partnership"),
    ent("U7", "DELTA TECH PTE LTD"),
])


def test_normalize_strips_legal_form_and_punctuation():
    assert normalize("Acme Engineering Pte. Ltd.") == "ACME ENGINEERING"
    assert normalize("BETA SOLUTIONS PRIVATE LIMITED") == "BETA SOLUTIONS"
    assert normalize("A & B (S) PTE LTD") == "A AND B S"
    assert normalize(None) == ""


def test_local_suffix():
    assert has_local_suffix("FOO PTE. LTD.")
    assert has_local_suffix("FOO PRIVATE LIMITED")
    assert has_local_suffix("FOO LLP")
    assert not has_local_suffix("FOO GMBH")
    assert not has_local_suffix("MINISTRY OF FOO")


def test_exact_former_and_punctuation_variants():
    m = {x.supplier_name: x for x in resolve(
        ["ACME ENGINEERING PTE LTD", "Beta Solutions Pte. Ltd.", "OLD BETA TRADING PTE. LTD."], INDEX)}
    assert m["ACME ENGINEERING PTE LTD"].method == "exact" and m["ACME ENGINEERING PTE LTD"].uen == "U1"
    assert m["Beta Solutions Pte. Ltd."].uen == "U2"
    assert m["OLD BETA TRADING PTE. LTD."].method == "former_name" and m["OLD BETA TRADING PTE. LTD."].uen == "U2"


def test_same_name_prefers_the_single_live_entity():
    m = resolve(["TWIN SERVICES PTE LTD"], INDEX)[0]
    assert m.uen == "U3" and m.method == "exact" and len(m.candidates) == 2


def test_legal_form_filter_llp_vs_company():
    llp, co = resolve(["DELTA TECH LLP", "DELTA TECH PTE LTD"], INDEX)
    assert llp.uen == "U6" and co.uen == "U7"


def test_fuzzy_match_and_subset_is_not_a_match():
    near = resolve(["GAMMA CONSTRUCTION AND ENGINEERING PTE LTD"], INDEX)[0]
    assert near.uen == "U5"  # normalises to the same key
    typo = resolve(["GAMMA CONSTRUCTON & ENGINEERING PTE LTD"], INDEX, strategies=("fuzzy",))[0]
    assert typo.method == "fuzzy" and typo.uen == "U5" and typo.confidence >= 0.92
    subset = resolve(["GAMMA PTE LTD"], INDEX, strategies=("fuzzy",))[0]
    assert subset.uen is None


def test_unresolved_vs_out_of_scope_and_no_llm_for_individuals():
    calls = []
    tb = lambda items: calls.append(items) or {}  # noqa: E731
    local, foreign, person = resolve(["ZZZ UNKNOWN PTE. LTD.", "ACME GMBH", "Tan Ah Kow"], INDEX, tiebreak=tb)
    assert local.method == "unresolved" and local.uen is None
    assert foreign.method == "out_of_scope"
    assert person.method == "out_of_scope"
    assert not calls  # nothing sendable: no candidates / individuals never go to the LLM


def test_llm_tiebreak_only_accepts_listed_candidates_and_caps_confidence():
    idx = EntityIndex([ent("A1", "SUNRISE LOGISTICS PTE LTD"), ent("A2", "SUNRISE LOGISTICS SERVICES PTE LTD")])
    tb = lambda items: {it["id"]: {"uen": "A2", "confidence": 0.99} for it in items}  # noqa: E731
    m = resolve(["SUNRISE LOGISTIC SVC PTE LTD"], idx, tiebreak=tb)[0]
    assert m.method == "llm_tiebreak" and m.uen == "A2" and m.confidence <= 0.85
    bad = lambda items: {it["id"]: {"uen": "NOT-A-CANDIDATE", "confidence": 0.9} for it in items}  # noqa: E731
    assert resolve(["SUNRISE LOGISTIC SVC PTE LTD"], idx, tiebreak=bad)[0].uen is None


@pytest.mark.parametrize("supplier,entity_name,entity_type,formers", [
    ("QUILLORA TEST TECH LLP", "QUILLORA TEST TECH PTE LTD", "Local Company", ()),
    ("QUILLORA TEST TECH PTE LTD", "QUILLORA TEST TECH LLP", "Limited Liability Partnership", ()),
    ("OLD QUILLORA TEST TECH LLP", "NEW QUILLORA TEST TECH PTE LTD", "Local Company", ("OLD QUILLORA TEST TECH",)),
])
def test_incompatible_legal_form_never_becomes_a_unique_name_match(supplier, entity_name, entity_type, formers):
    index = EntityIndex([ent("TEST-ONLY", entity_name, etype=entity_type, formers=formers)])
    match = resolve([supplier], index)[0]
    assert match.uen is None
    assert match.method == "unresolved"


def test_expanded_legal_suffix_and_branch_name_use_the_same_identity():
    index = EntityIndex([
        ent("TEST-CO", "QUILLORA TEST ENGINEERING PTE. LTD."),
        ent("TEST-BRANCH", "QUILLORA TEST INTERNATIONAL (SINGAPORE BRANCH)", etype="Foreign Company Branch"),
    ])
    company, branch = resolve([
        "Quillora Test Engineering Private Limited",
        "Quillora Test International (Singapore Branch)",
    ], index)
    assert company.uen == "TEST-CO"
    assert branch.uen == "TEST-BRANCH"
