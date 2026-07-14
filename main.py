from utils.csv_reader import process_all_datasets, create_analytical_df, load_and_process_dataset, extract_kpis
from utils.html_generator import generate_html_report

file_path = "data/dataset_01_parceiroA.csv"


if __name__ == "__main__":
    #process_all_datasets()
    df = load_and_process_dataset(file_path)
    #analytical_df = create_analytical_df(df)
    KPIs = extract_kpis(df)
    print(KPIs)
    generate_html_report(KPIs)
    #print(analytical_df)
    #print(KPIs)
