import os
import glob
import asyncio
import httpx
import json
import re
import pandas as pd
from tqdm.asyncio import tqdm as tqdm_async
from dotenv import load_dotenv

load_dotenv()


# --- КОНФИГУРАЦИЯ ---
AI_MODEL = os.getenv("AI_MODEL", "llama3.2:3b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
SEM = asyncio.Semaphore(1)


def clean_ai_response(text):
    if not text:
        return "Не определено"
    text = re.sub(r'[^а-яА-ЯёЁ0-9\s|\-]', '', text)
    text = " ".join(text.split())
    return text[:50]


def convert_to_hms(total_hours):
    if pd.isna(total_hours) or total_hours < 0:
        return "00:00:00"
    total_seconds = int(round(total_hours * 3600))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


async def get_ai_conclusion(client: httpx.AsyncClient, descr: str, message: str, category: str) -> dict:
    clean_descr = str(descr or "Нет описания").strip()
    clean_message = str(message or "Нет логов").strip()

    async with SEM:
        try:
            prompt = (
                f"Ты — Ведущий Экспер IT '{category}'. "
                f"your prompt:\n"
            )

            res = await client.post(OLLAMA_URL, json={
                "model": AI_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 70,
                    "top_p": 0.1,
                    "stop": ["\n"]
                }
            }, timeout=60.0)

            if res.status_code != 200:
                return {"root_cause": "Ошибка сервера", "resolution": "Ошибка сервера"}

            raw_ans = res.json().get('response', '{}')

            # Попытка вытащить JSON из ответа
            match = re.search(r'\{.*}', raw_ans, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return {
                    "root_cause": clean_ai_response(data.get("root_cause", "Не определено")),
                    "resolution": clean_ai_response(data.get("resolution", "Не определено"))
                }
            return {"root_cause": "Не определено", "resolution": "Не определено"}

        except Exception as e:
            print(f"Ошибка AI: {e}")
            return {"root_cause": "Ошибка", "resolution": "Ошибка"}


async def process_category(df, cat_name, week_label):
    if df is None or df.empty:
        print(f"--- Пропуск {cat_name}: данных нет ---")
        return

    # Защита от пробелов в названиях колонок (KeyError)
    df.columns = df.columns.str.strip()

    out_dir = os.path.join(os.getenv("FINAL_EXPORT_PATH", "./final_reports"), cat_name)
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, f"Report_{cat_name}_{week_label}.xlsx")

    if os.path.exists(out_file):
        print(f"✅ Отчет {cat_name} уже готов: {out_file}")
        return

    # Уникализация по комбинации
    df['KEY'] = df['DESCR'].fillna('') + df['MESSAGE'].fillna('')
    unique_df = df.drop_duplicates(subset=['KEY']).copy()

    print(f"\n>>> Анализ {cat_name}: {len(df)} заявок (уникальных: {len(unique_df)})")

    # Запуск AI
    async with httpx.AsyncClient(timeout=90.0) as client:
        tasks = [
            get_ai_conclusion(client, row['DESCR'], row['MESSAGE'], cat_name)
            for _, row in unique_df.iterrows()
        ]
        results = await tqdm_async.gather(*tasks, desc=f"🤖 Обработка {cat_name}")

        # Создаем временный DataFrame из результатов
        res_df = pd.DataFrame(results)

        # Исправляем опечатку (было 'resolotion', нужно 'resolution')
        if 'root_cause' not in res_df.columns:
            res_df['root_cause'] = "Не определено"
        if 'resolution' not in res_df.columns:  # ИСПРАВЛЕНО
            res_df['resolution'] = "Не определено"

        unique_df['AI_RootCause'] = res_df['root_cause'].values
        unique_df['AI_Resolution'] = res_df['resolution'].values

    # 4. Сопоставляем обратно в основной df
    root_map = dict(zip(unique_df['KEY'], unique_df['AI_RootCause']))
    res_map = dict(zip(unique_df['KEY'], unique_df['AI_Resolution']))

    df['AI_RootCause'] = df['KEY'].map(root_map)
    df['AI_Resolution'] = df['KEY'].map(res_map)

    cols_to_drop = ['KEY']
    df.drop(columns=cols_to_drop, inplace=True, errors='ignore')

    # Расчет времени
    df['CREATED_DT'] = pd.to_datetime(df['TICKET_CREATED'], format='%d.%m.%Y %H:%M', errors='coerce')
    df['CLOSED_DT'] = pd.to_datetime(df['TICKET_CLOSED'], format='%d.%m.%Y %H:%M', errors='coerce')
    df['DURATION_HOURS'] = (df['CLOSED_DT'] - df['CREATED_DT']).dt.total_seconds() / 3600

    # Сводная
    summary = df.groupby(['TEH']).agg({'ID_TICKET': 'count', 'DURATION_HOURS': 'mean'}).reset_index()
    summary['AVER TIME'] = summary['DURATION_HOURS'].apply(convert_to_hms)
    summary = summary.sort_values(by='ID_TICKET', ascending=False).drop(columns=['DURATION_HOURS'])
    summary = summary.rename(columns={'ID_TICKET': 'Кол-во заявок'})

    # Сохранение
    with pd.ExcelWriter(out_file, engine='xlsxwriter') as writer:
        summary.to_excel(writer, sheet_name='Сводная', index=False)
        df.drop(columns=['CREATED_DT', 'CLOSED_DT', 'DURATION_HOURS'],
                errors='ignore', inplace=True)
        df.to_excel(writer, sheet_name='Анализ', index=False)
    print(f"💾 Успешно сохранено: {out_file}")


def main():
    raw_dir = r"your dir"
    files = glob.glob(os.path.join(raw_dir, "raw_week_*.parquet"))
    if not files:
        print("❌ Ошибка: Нет файлов .parquet.")
        return

    input_file = max(files, key=os.path.getctime)
    week_label = os.path.basename(input_file).replace("raw_week_", "").replace(".parquet", "")
    df_all = pd.read_parquet(input_file).drop_duplicates(subset=['ID_TICKET'])

    omni_pattern = 'OMNI'
    df_omni = df_all[df_all['TEH'].fillna('').str.contains(omni_pattern, case=False)].copy()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if not df_omni.empty:
        loop.run_until_complete(process_category(df_omni, "OMNI", week_label))
    print("\n✅ Готово.")


if __name__ == "__main__":
    main()
