# SAMPLE ATTACHMENT FILE - DELETE THIS AND ADD YOUR REAL ATTACHMENTS

## Expected Format

Place your attachment files here as Excel (.xlsx) or CSV (.csv) files.

### Example Files:
- `EM-Codes-for-Injcodes.xlsx` - E/M codes for injection services
- `Inclusive-supply-codes-Policy-List.xlsx` - Supply codes included in procedures
- `Global-Days-Surgical-Codes.csv` - Surgical codes with global periods

### Expected Columns:

For code list attachments:
| CPT_Code | Description | Modifier | Notes |
|----------|-------------|----------|-------|
| 99213    | Office visit| 25       | ...   |

For age/frequency limits:
| Code | Min_Age | Max_Age | Max_Units | Per_Period |
|------|---------|---------|-----------|------------|
| 96372| 0       | 999     | 4         | day        |

### Processing

Agent 0 will analyze these attachments and generate metadata in `output_metadata/`
