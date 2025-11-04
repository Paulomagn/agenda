import os
import requests
from datetime import datetime, timedelta, timezone

# Configurações
SUPABASE_URL = "https://vggalxjocgvgoxcrhpzh.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZnZ2FseGpvY2d2Z294Y3JocHpoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIyMTAwNjgsImV4cCI6MjA3Nzc4NjA2OH0.mMX0_Un1Ic5Z717CzHRadLMDyBe28-9b_5NCzm7vfgQ"
TELEGRAM_BOT_TOKEN = "8593565188:AAFc1gvWDk6njaay3cmgOqhCg1oljJaHqv4"
# Alerta 15 minutos antes do evento
ALERT_MINUTES_BEFORE = 15

def format_timestamp(dt):
    """Formata o datetime para o formato ISO 8601 com 'Z' (Zulu/UTC) para PostgREST."""
    # Remove microsegundos e adiciona 'Z'
    return dt.replace(microsecond=0).isoformat().replace('+00:00', 'Z')

def get_events_to_alert():
    """Busca eventos no Supabase que estão próximos e ainda não foram alertados."""
    now_utc = datetime.now(timezone.utc)
    
    # Define o limite de tempo para buscar eventos (agora até ALERT_MINUTES_BEFORE no futuro)
    time_limit = now_utc + timedelta(minutes=ALERT_MINUTES_BEFORE)

    now_formatted = format_timestamp(now_utc)
    time_limit_formatted = format_timestamp(time_limit)

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    # Construindo a URL com os filtros
    # event_time=gte.{now_formatted} (Maior ou igual ao tempo atual)
    # event_time=lte.{time_limit_formatted} (Menor ou igual ao limite de tempo)
    # alert_sent=eq.false (Ainda não alertado)
    url = (
        f"{SUPABASE_URL}/rest/v1/events?select=id,title,description,event_time,telegram_chat_id"
        f"&event_time=gte.{now_formatted}"
        f"&event_time=lte.{time_limit_formatted}"
        f"&alert_sent=eq.false"
    )

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar eventos no Supabase: {e}")
        print(f"URL da requisição: {url}")
        if response is not None:
            print(f"Resposta do Supabase: {response.text}")
        return []

def send_telegram_alert(chat_id, event):
    """Envia uma mensagem de alerta para o Telegram."""
    # O Supabase retorna a data em UTC. O fuso horário local é inferido pelo sistema.
    # Para simplificar, vamos exibir a hora como está no banco de dados (UTC)
    # O usuário deve inserir a hora no site já considerando o fuso horário.
    event_time_utc = datetime.fromisoformat(event['event_time'].replace('Z', '+00:00'))
    
    message = (
        f"🔔 *ALERTA DE AGENDA - {ALERT_MINUTES_BEFORE} MINUTOS*\n\n"
        f"📅 *Evento:* {event['title']}\n"
        f"🕒 *Hora (UTC):* {event_time_utc.strftime('%H:%M de %d/%m/%Y')}\n"
        f"📝 *Descrição:* {event['description'] or 'Nenhuma'}"
    )

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }

    try:
        response = requests.post(telegram_url, data=payload)
        response.raise_for_status()
        return response.json().get('ok', False)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem para o Telegram: {e}")
        return False

def mark_event_as_sent(event_id):
    """Marca o evento como alertado no Supabase."""
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=minimal'
    }
    
    data = {'alert_sent': True}
    url = f"{SUPABASE_URL}/rest/v1/events?id=eq.{event_id}"

    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Erro ao marcar evento como enviado: {e}")
        return False

def main():
    """Função principal para verificar e enviar alertas."""
    print(f"Iniciando verificação de eventos às {datetime.now().isoformat()}")
    events = get_events_to_alert()
    
    if not events:
        print("Nenhum evento próximo encontrado.")
        return

    print(f"Encontrados {len(events)} eventos próximos.")
    
    for event in events:
        chat_id = event.get('telegram_chat_id')
        if chat_id:
            if send_telegram_alert(chat_id, event):
                print(f"Alerta enviado com sucesso para o evento: {event['title']}")
                mark_event_as_sent(event['id'])
            else:
                print(f"Falha ao enviar alerta para o evento: {event['title']}")
        else:
            print(f"Evento {event['title']} sem ID de chat. Pulando.")

if __name__ == '__main__':
    main()
