import json
import datetime
import time
import os
from atproto import Client
import logging
import pickle

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='import_log.txt'
)
logger = logging.getLogger(__name__)

# Arquivo para salvar progresso
PROGRESS_FILE = "import_progress.pkl"

class ImportProgress:
    def __init__(self):
        self.completed_tweets = []
        self.last_index = 0
        self.total_tweets = 0
        
    def save(self):
        with open(PROGRESS_FILE, 'wb') as f:
            pickle.dump(self, f)
    
    @staticmethod
    def load():
        try:
            with open(PROGRESS_FILE, 'rb') as f:
                return pickle.load(f)
        except:
            return ImportProgress()

# Remover credenciais hardcoded
BSKY_CHAR_LIMIT = 300

def test_auth(handle, password):
    """Testa autenticação com credenciais fornecidas"""
    try:
        client = Client()
        clean_handle = handle.strip()
        clean_password = password.strip()
        
        logger.info(f"Tentando conexão com Bluesky usando handle: {clean_handle}")
        response = client.login(clean_handle, clean_password)
        
        if response and hasattr(response, 'success') and not response.success:
            raise Exception("Login falhou - resposta indica falha")
            
        logger.info("Login bem-sucedido!")
        return client
    except Exception as e:
        logger.error(f"Erro na autenticação: {str(e)}")
        return None

def load_tweets(file_path):
    """Carrega tweets de um arquivo JSON exportado e ordena por data."""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
        print(f"Carregando tweets de: {file_path}")
        with open(file_path, encoding="utf-8") as f:
            content = f.read().replace("window.YTD.tweets.part0 = ", "")
            tweets = json.loads(content)
            
        # Ordenar tweets por data (mais antigo primeiro)
        tweets.sort(key=lambda x: datetime.datetime.strptime(
            x['tweet']['created_at'], 
            "%a %b %d %H:%M:%S %z %Y"
        ))
        
        print(f"Carregados e ordenados {len(tweets)} tweets (do mais antigo ao mais novo)")
        return tweets
    except Exception as e:
        print(f"Erro ao carregar tweets: {e}")
        return []

def truncate_text(text, limit):
    """Trunca texto para caber no limite de caracteres do Bluesky."""
    if len(text) > limit:
        return text[:limit - 3] + "..."
    return text

def check_duplicate_post(client, text, limit=100):
    """Verifica se o texto já foi postado no Bluesky"""
    try:
        # Buscar posts recentes do usuário
        response = client.get_author_feed(client.me.did, limit=limit)
        posts = response.feed
        
        # Limpar texto para comparação
        clean_text = text.lower().strip()
        
        # Verificar cada post
        for post in posts:
            existing_text = post.post.record.text.lower().strip()
            # Remover footers para comparação
            existing_text = existing_text.split("\n\n📱")[0].strip()
            clean_text = clean_text.split("\n\n📱")[0].strip()
            
            if clean_text in existing_text or existing_text in clean_text:
                return True
                
        return False
    except Exception as e:
        logger.error(f"Erro ao verificar posts duplicados: {e}")
        return False

def post_tweet_to_bsky(client, tweet, simulate=False):
    """Posta um tweet com mídia (se disponível) no BlueSky."""
    text = tweet.get("full_text", "")
    
    print(f"\nAnalisando tweet: {text[:100]}...")
    
    # Verificar se já foi postado
    if check_duplicate_post(client, text):
        return False, "Tweet já foi postado anteriormente no Bluesky"
    
    # Verificações iniciais
    if not text:
        return False, "Tweet sem texto"
        
    # Novas verificações para ignorar posts específicos
    textos_ignorados = [
        "usuários que não te seguem de volta encontrado!",
        "Pergunte-me qualquer coisa"
    ]
    
    for texto in textos_ignorados:
        if texto.lower() in text.lower():
            return False, f"Post ignorado: contém '{texto}'"
            
    if tweet.get("retweeted"):
        return False, "É um retweet"
    if text.startswith("RT @"):
        return False, "É um retweet (começa com RT @)"
    if text.startswith("@"):
        return False, "É uma resposta (começa com @)"

    # Verificar se há mídia
    media_entities = tweet.get("extended_entities", {}).get("media", [])
    has_media = bool(media_entities)
    
    if has_media:
        print(f"📷 Tweet contém {len(media_entities)} mídia(s)")
        try:
            # Tentar fazer upload da primeira mídia apenas
            media = media_entities[0]
            media_url = media.get("media_url_https")
            if media_url:
                print(f"🔄 Tentando fazer upload da mídia: {media_url}")
                # Aqui você implementaria o upload da mídia
                # Por enquanto, vamos apenas indicar que há mídia
                text = f"{text}\n\n🖼️ [Imagem do tweet original]"
        except Exception as e:
            print(f"⚠️ Erro ao processar mídia: {e}")

    # Criar footers com diferentes tamanhos
    try:
        tweet_date = datetime.datetime.strptime(tweet.get("created_at"), "%a %b %d %H:%M:%S %z %Y")
        date_str = tweet_date.strftime("%d/%m/%Y às %H:%M")
        
        # Footer completo
        footer_completo = f"\n\n📱 Post importado do Twitter\n📅 Publicado originalmente em {date_str}\n🔄 Migrado via script"
        
        # Footer médio
        footer_medio = f"\n\n📱 Twitter • {date_str}"
        
        # Footer mínimo
        footer_minimo = f"\n\n📱 {date_str}"
        
    except:
        footer_completo = "\n\n📱 Post importado do Twitter"
        footer_medio = "\n\n📱 Twitter"
        footer_minimo = "\n\n📱"

    # Tentar usar o footer mais apropriado baseado no espaço disponível
    if len(text) <= BSKY_CHAR_LIMIT - len(footer_completo):
        footer = footer_completo
        full_text = text + footer
    elif len(text) <= BSKY_CHAR_LIMIT - len(footer_medio):
        footer = footer_medio
        full_text = text + footer
    elif len(text) <= BSKY_CHAR_LIMIT - len(footer_minimo):
        footer = footer_minimo
        full_text = text + footer
    else:
        # Se ainda assim não couber, truncar o texto
        text = text[:BSKY_CHAR_LIMIT - len(footer_minimo) - 3] + "..."
        full_text = text + footer_minimo

    try:
        if simulate:
            print(f"[SIMULAÇÃO] Postando:\n{full_text}")
        else:
            client.post(text=full_text)
            print(f"✅ Postado com sucesso:\n{full_text}")
        return True, "Sucesso"
    except AttributeError:
        print("⚠️ Erro: Método de postagem não encontrado. Tentando método alternativo...")
        try:
            # Método alternativo de postagem
            client.com.atproto.repo.create_record(
                collection='app.bsky.feed.post',
                repo=client.me.did,
                record={
                    'text': full_text,
                    'createdAt': datetime.datetime.now().isoformat(),
                    '$type': 'app.bsky.feed.post'
                }
            )
            print(f"✅ Postado com sucesso (método alternativo): {full_text}")
            return True, "Sucesso (método alternativo)"
        except Exception as e:
            reason = f"Erro no método alternativo: {str(e)}"
            print(f"❌ {reason}")
            return False, reason
    except Exception as e:
        reason = f"Erro ao postar: {str(e)}"
        print(f"❌ {reason}")
        return False, reason

def upload_old_tweets(client, tweets, callback=None, simulate=False, batch_size=50):
    """Faz upload de tweets com suporte a retomada"""
    progress = ImportProgress.load()
    
    if progress.total_tweets != len(tweets):
        progress.total_tweets = len(tweets)
        progress.last_index = 0
        progress.completed_tweets = []
    
    start_index = progress.last_index
    total_tweets = len(tweets)
    
    try:
        while start_index < total_tweets:
            end_index = min(start_index + batch_size, total_tweets)
            current_batch = tweets[start_index:end_index]
            
            for index, tweet_data in enumerate(current_batch):
                current_position = start_index + index + 1
                
                # Pular tweets já processados
                if tweet_data in progress.completed_tweets:
                    continue
                    
                try:
                    tweet = tweet_data.get("tweet")
                    if not tweet:
                        continue
                        
                    progress_pct = (current_position / total_tweets) * 100
                    
                    success, reason = post_tweet_to_bsky(client, tweet, simulate=simulate)
                    
                    if success:
                        progress.completed_tweets.append(tweet_data)
                        progress.last_index = current_position
                        progress.save()
                    
                    if callback:
                        callback(progress_pct, success, reason)
                    
                    time.sleep(3 if success else 5)
                        
                except Exception as e:
                    logger.error(f"Erro ao processar tweet {current_position}: {e}")
                    time.sleep(10)
                    continue
            
            start_index += batch_size
            if start_index < total_tweets:
                time.sleep(60)
                
    except KeyboardInterrupt:
        progress.save()
        logger.info(f"Processo interrompido. Progresso salvo no tweet {current_position}")
        return progress
    
    return progress

def filter_tweets(tweets, keyword=None, start_date=None, end_date=None):
    """Filtra tweets por palavra-chave ou intervalo de datas."""
    filtered = []
    for tweet_data in tweets:
        tweet = tweet_data.get("tweet")
        if not tweet:
            continue
        if keyword and keyword not in tweet.get("full_text", ""):
            continue
        if start_date or end_date:
            tweet_date = datetime.datetime.strptime(tweet.get("created_at"), "%a %b %d %H:%M:%S %z %Y")
            if start_date and tweet_date < start_date:
                continue
            if end_date and tweet_date > end_date:
                continue
        filtered.append(tweet_data)
    return filtered

def warning():
    """Exibe um aviso antes de executar o script."""
    print("\nAVISO: Este script pode SPAMAR as timelines dos seus seguidores.")
    print("Recomenda-se usar uma conta nova.")
    response = input("Digite [EU ENTENDO] para continuar: ")
    if (response.strip() != "EU ENTENDO"):
        print("Saindo...")
        exit()

def create_session_file(tweets_path, handle):
    """Cria/atualiza arquivo de sessão para retomada"""
    session_file = f"session_{handle.replace('.', '_')}.json"
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            return json.load(f)
    return {
        'tweets_path': tweets_path,
        'last_index': 0,
        'completed': [],
        'total': 0
    }

def save_session(session_data, handle):
    """Salva estado da sessão"""
    session_file = f"session_{handle.replace('.', '_')}.json"
    with open(session_file, 'w') as f:
        json.dump(session_data, f)

class RateLimiter:
    def __init__(self):
        self.base_delay = 1.0  # Reduzido para 1 segundo
        self.current_delay = 1.0
        self.max_delay = 5.0   # Reduzido para 5 segundos
        self.min_delay = 0.5   # Reduzido para 0.5 segundos
        self.success_count = 0
        self.error_count = 0
        
    def adapt_delay(self, success):
        if success:
            self.success_count += 1
            self.error_count = 0
            # Reduz o delay após 3 sucessos consecutivos
            if self.success_count >= 3:
                self.current_delay = max(self.min_delay, self.current_delay * 0.7)
                self.success_count = 0
        else:
            self.error_count += 1
            self.success_count = 0
            # Aumenta o delay em caso de erro
            self.current_delay = min(self.max_delay, self.current_delay * 1.2)
            
    def wait(self):
        time.sleep(self.current_delay)

def resume_import(handle, password, tweets_path, callback=None):
    """Função principal de importação com suporte a retomada"""
    session = create_session_file(tweets_path, handle)
    rate_limiter = RateLimiter()
    
    try:
        client = test_auth(handle, password)
        if not client:
            return False, "Falha na autenticação"

        tweets = load_tweets(tweets_path)
        if not tweets:
            return False, "Nenhum tweet encontrado"

        total_tweets = len(tweets)
        
        # Notificar total inicial
        if callback:
            callback(0, True, {
                'text': '',
                'status': 'Iniciando',
                'current': session['last_index'],
                'total': total_tweets,
                'analyzing': True
            })

        logger.info(f"Retomando importação a partir do índice {session['last_index']} de {total_tweets} tweets")
        
        for i in range(session['last_index'], total_tweets):
            # Verificar flag de parada
            if getattr(callback, 'stop_requested', False):
                logger.info(f"Parada solicitada no índice {i}")
                session['last_index'] = i
                save_session(session, handle)
                return True, "Importação pausada pelo usuário"

            try:
                tweet = tweets[i]['tweet']
                text = tweet.get('full_text', '')
                current_position = i + 1
                
                # Notificar análise
                if callback:
                    callback(
                        ((current_position) / total_tweets) * 100,
                        True,
                        {
                            'text': text,
                            'status': 'Analisando',
                            'current': current_position,
                            'total': total_tweets,
                            'analyzing': True
                        }
                    )
                
                # Verificações de skip
                if any(check in text.lower() for check in ['rt @', '@', 'pergunte-me']):
                    reason = "É um retweet" if 'rt @' in text.lower() else \
                            "É uma resposta" if text.startswith('@') else \
                            "Post ignorado: contém 'Pergunte-me qualquer coisa'"
                    if callback:
                        callback(((i + 1) / len(tweets)) * 100, False, reason)
                    continue

                # Rate limiting adaptativo
                rate_limiter.wait()
                
                success, reason = post_tweet_to_bsky(client, tweet)
                rate_limiter.adapt_delay(success)
                
                # Callback com informações completas
                if callback:
                    callback(((i + 1) / len(tweets)) * 100, success, {
                        'text': text,
                        'status': reason,
                        'delay': rate_limiter.current_delay,
                        'footer': f"\n\n📱 Post importado do Twitter\n📅 {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}\n🔄 Migrado via script"
                    })

                if success:
                    session['completed'].append(tweet.get('id_str'))
                    session['last_index'] = i + 1  # Incrementar após sucesso
                    save_session(session, handle)

            except Exception as e:
                logger.error(f"Erro no tweet {i}: {str(e)}")
                if callback:
                    callback(
                        ((i + 1) / total_tweets) * 100,
                        False,
                        {
                            'error': str(e),
                            'current': i + 1,
                            'total': total_tweets
                        }
                    )
                continue

        return True, "Importação concluída"

    except Exception as e:
        logger.error(f"Erro na importação: {str(e)}")
        return False, str(e)

def main():
    """Função principal do script."""
    warning()

    # Verificações iniciais
    handle = input("Digite seu handle do Bluesky: ")
    password = input("Digite seu App Password do Bluesky: ")

    if not handle or not password:
        print("Handle ou App Password não configurados!")
        return

    # Testar autenticação primeiro
    print("\nTestando autenticação...")
    client = test_auth(handle, password)
    if not client:
        print("Falha na autenticação. Verifique suas credenciais.")
        return

    tweets = load_tweets(TWEETS_JS_PATH)
    if not tweets:
        print("Nenhum tweet encontrado. Verifique o arquivo e tente novamente.")
        return

    # Filtrar tweets (opcional)
    start_date = datetime.datetime(2022, 1, 1, tzinfo=datetime.timezone.utc)
    filtered_tweets = filter_tweets(tweets)  # Removido filtro de keyword para teste
    
    print(f"\nTweets ordenados do mais antigo ({filtered_tweets[0]['tweet']['created_at']})")
    print(f"para o mais novo ({filtered_tweets[-1]['tweet']['created_at']})")

    # Alterado para False para postar de verdade
    simulate_mode = False
    
    # Confirmação final antes de começar
    if not simulate_mode:
        print("\nMODO DE POSTAGEM REAL ATIVADO!")
        confirm = input("Digite [POSTAR] para começar a postar de verdade: ")
        if confirm.strip() != "POSTAR":
            print("Operação cancelada.")
            return
    
    upload_old_tweets(client, filtered_tweets, simulate=simulate_mode, batch_size=100)

if __name__ == "__main__":
    main()