import pandas as pd
import matplotlib.pyplot as plt

def plot_sales_trend(df, output_path, title="Täglicher Umsatzverlauf mit 7- und 30-Tage gleitendem Durchschnitt"):
    # Timestamp in Datum umwandeln (Tagsebene)
    df = df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp']).dt.date

    # Umsatz pro Tag summieren
    daily_sales = df.groupby('Timestamp')['Value'].sum().reset_index()

    # Index auf Timestamp setzen und DatetimeIndex erstellen
    daily_sales['Timestamp'] = pd.to_datetime(daily_sales['Timestamp'])
    daily_sales = daily_sales.set_index('Timestamp')

    # Zeitindex komplett machen (von erstem bis letztem Tag)
    full_index = pd.date_range(start=daily_sales.index.min(), end=daily_sales.index.max(), freq='D')

    # Fehlende Tage mit Umsatz 0 auffüllen
    daily_sales = daily_sales.reindex(full_index, fill_value=0)

    # 7-Tage gleitenden Durchschnitt berechnen
    daily_sales['MA7'] = daily_sales['Value'].rolling(window=7, min_periods=1).mean()

    # 30-Tage (monatlichen) gleitenden Durchschnitt berechnen
    daily_sales['MA30'] = daily_sales['Value'].rolling(window=30, min_periods=1).mean()

    # Plot erstellen
    plt.figure(figsize=(12,6))
    plt.plot(daily_sales.index, daily_sales['Value'], alpha=0.3, label='Täglicher Umsatz')
    plt.plot(daily_sales.index, daily_sales['MA7'], color='red', label='7-Tage gleitender Durchschnitt', linewidth=2)
    plt.plot(daily_sales.index, daily_sales['MA30'], color='green', label='30-Tage gleitender Durchschnitt', linewidth=2)
    plt.title(title)
    plt.xlabel('Datum')
    plt.ylabel('Summe Umsatz pro Tag')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()

    # Plot als JPG speichern
    plt.savefig(output_path, format='jpg', dpi=300)
    plt.close()