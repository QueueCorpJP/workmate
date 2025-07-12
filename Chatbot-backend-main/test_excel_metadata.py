import importlib, sys, json, asyncio

# --- helper to monkeypatch supabase_adapter.insert_data ---
class DummyResult:
    def __init__(self, data):
        self.data = [data]


def test_record_document_source_metadata(monkeypatch):
    # Dynamically import target module
    api_module = importlib.import_module("modules.knowledge.api")

    # Prepare fake insert_data to capture payload
    captured = {}

    def fake_insert(table: str, data: dict):
        captured.update(data)
        return DummyResult(data)

    # Monkeypatch the insert_data function inside supabase_adapter
    supabase_adapter = importlib.import_module("supabase_adapter")
    monkeypatch.setattr(supabase_adapter, "insert_data", fake_insert)

    # Run the async helper
    metadata_json = json.dumps({
        "columns": ["発行予定日", "受注日", "完了日"],
        "date_types": {"発行予定日": "issue_date", "受注日": "order_date", "完了日": "completion_date"}
    }, ensure_ascii=False)
    
    # Create a mock database connection
    class MockDB:
        def commit(self):
            pass
    
    # Execute the function
    asyncio.run(api_module._record_document_source(
        name="test.xlsx",
        doc_type="EXCEL", 
        page_count=1,
        content="test content",
        user_id="test_user",
        company_id="test_company",
        db=MockDB(),
        metadata_json=metadata_json
    ))
    
    # Verify the captured data
    assert "metadata" in captured, "metadata field missing"
    assert captured["metadata"] == metadata_json, f"Expected {metadata_json}, got {captured.get('metadata')}"
    
    # Parse and verify JSON content
    parsed_metadata = json.loads(captured["metadata"])
    assert "columns" in parsed_metadata, "columns missing from metadata"
    assert "date_types" in parsed_metadata, "date_types missing from metadata"
    assert len(parsed_metadata["columns"]) == 3, f"Expected 3 columns, got {len(parsed_metadata['columns'])}"
    assert len(parsed_metadata["date_types"]) == 3, f"Expected 3 date_types, got {len(parsed_metadata['date_types'])}"
    
    print("✅ Test passed: metadata correctly saved with columns and date_types") 