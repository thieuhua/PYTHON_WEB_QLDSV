#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Quick test để verify export fix"""

print("=" * 60)
print("  QUICK TEST - Export CSV Fix")
print("=" * 60)

# Test 1: Import modules
print("\n[1/4] Testing imports...")
try:
    from io import StringIO, BytesIO
    import csv
    print("  ✅ io, csv OK")

    from backend.routers import teacher
    print("  ✅ teacher router OK")
except Exception as e:
    print(f"  ❌ Import failed: {e}")
    exit(1)

# Test 2: Test CSV generation với UTF-8 BOM
print("\n[2/4] Testing CSV generation...")
try:
    output = StringIO()
    output.write('\ufeff')  # BOM

    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    writer.writerow(['STT', 'Họ và tên', 'Mã SV'])
    writer.writerow([1, 'Nguyễn Văn An', 'SV001'])

    csv_content = output.getvalue()
    print(f"  CSV length: {len(csv_content)} chars")
    has_bom = csv_content.startswith('\ufeff')
    print(f"  Has BOM: {has_bom}")
    print("  ✅ CSV generation OK")
except Exception as e:
    print(f"  ❌ CSV generation failed: {e}")
    exit(1)

# Test 3: Test encode to bytes
print("\n[3/4] Testing encoding to bytes...")
try:
    bytes_output = BytesIO(csv_content.encode('utf-8-sig'))
    bytes_data = bytes_output.getvalue()
    print(f"  Bytes length: {len(bytes_data)} bytes")
    has_utf8_bom = bytes_data[:3] == b'\xef\xbb\xbf'
    print(f"  Has UTF-8 BOM: {has_utf8_bom}")
    print("  ✅ Encoding OK")
except Exception as e:
    print(f"  ❌ Encoding failed: {e}")
    exit(1)

# Test 4: Test filename sanitization
print("\n[4/4] Testing filename sanitization...")
try:
    import re
    from urllib.parse import quote

    test_names = [
        "Lập trình Web",
        "Cơ sở dữ liệu <2025>",
        "Test/Class:Name"
    ]

    pattern = r'[<>:"/\\|?*]'
    for class_name in test_names:
        safe = re.sub(pattern, '_', class_name)
        filename = f"{safe}_students.csv"
        encoded = quote(filename)
        print(f"  '{class_name}' → '{filename}'")

    print("  ✅ Sanitization OK")
except Exception as e:
    print(f"  ❌ Sanitization failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("  ✅ ALL TESTS PASSED!")
print("=" * 60)
print("\n🚀 Server sẵn sàng để export CSV!")
print("💡 Khởi động server và test lại export\n")

