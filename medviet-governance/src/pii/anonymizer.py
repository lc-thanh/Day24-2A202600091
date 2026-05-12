# src/pii/anonymizer.py
import hashlib
import random
import pandas as pd
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


def fake_cccd() -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(12))


def fake_phone() -> str:
    return f"0{random.choice(['3', '5', '7', '8', '9'])}" + "".join(
        str(random.randint(0, 9)) for _ in range(8)
    )

class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        TODO: Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : Nguyen Van A → N****** V** A
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        - "generalize": chỉ dùng cho tuổi/năm sinh
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        # TODO: implement operators dict dựa trên strategy
        operators = {}

        if strategy == "replace":
            operators = {
                "PERSON": OperatorConfig("replace", 
                          {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace",
                                 {"new_value": fake.email()}),   # TODO: fake email
                "VN_CCCD": OperatorConfig("replace",
                           {"new_value": fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace",
                            {"new_value": fake_phone()}),
            }
        elif strategy == "mask":
            # TODO: implement masking
            operators = {
                "DEFAULT": OperatorConfig("mask", {
                    "masking_char": "*",
                    "chars_to_mask": 8,
                    "from_end": False
                })
            }
        elif strategy == "hash":
            # TODO: implement hashing dùng sha256
            operators = {
                "DEFAULT": OperatorConfig("custom", {
                    "lambda": lambda value: hashlib.sha256(value.encode()).hexdigest()
                })
            }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        TODO: Anonymize toàn bộ DataFrame.
        - Cột text (ho_ten, dia_chi, email): dùng anonymize_text()
        - Cột cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - Cột benh, ket_qua_xet_nghiem: GIỮ NGUYÊN (cần cho model training)
        - Cột patient_id: GIỮ NGUYÊN (pseudonym đã đủ an toàn)
        """
        df_anon = df.copy()

        # TODO: Xử lý từng cột PII
        # Gợi ý: dùng df.apply() hoặc list comprehension
        def replacement_series(column: str, generator) -> list:
            original_values = set(df[column].astype(str))
            replacements = []
            for _ in range(len(df_anon)):
                value = str(generator())
                while value in original_values:
                    value = str(generator())
                replacements.append(value)
            return replacements

        if "ho_ten" in df_anon.columns:
            df_anon["ho_ten"] = replacement_series("ho_ten", fake.name)
        if "dia_chi" in df_anon.columns:
            df_anon["dia_chi"] = replacement_series("dia_chi", fake.address)
        if "email" in df_anon.columns:
            df_anon["email"] = replacement_series("email", fake.email)
        if "cccd" in df_anon.columns:
            df_anon["cccd"] = replacement_series("cccd", fake_cccd)
        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = replacement_series("so_dien_thoai", fake_phone)
        if "bac_si_phu_trach" in df_anon.columns:
            df_anon["bac_si_phu_trach"] = replacement_series("bac_si_phu_trach", fake.name)

        return df_anon

    def calculate_detection_rate(self, 
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        TODO: Tính % PII được detect thành công.
        Mục tiêu: > 95%

        Logic: với mỗi ô trong pii_columns,
               kiểm tra xem detect_pii() có tìm thấy ít nhất 1 entity không.
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                normalized_value = value
                if col == "cccd" and value.isdigit():
                    normalized_value = value.zfill(12)
                elif col == "so_dien_thoai" and value.isdigit() and len(value) == 9:
                    normalized_value = f"0{value}"

                results = detect_pii(normalized_value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
