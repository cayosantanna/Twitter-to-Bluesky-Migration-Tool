# 🐦 Twitter-to-Bluesky-Migration-Tool 🌌

## 📜 Descrição
Esta é uma aplicação desenvolvida para facilitar a transição entre as redes sociais **Twitter** e **Bluesky**. Sabemos que pode ser difícil migrar dados de uma plataforma para outra, por isso criamos este script que permite exportar seus tweets, desde os mais antigos até os mais recentes, para o Bluesky.

---

## ✨ Funcionalidades principais

1. **📋 Exportação de tweets:** Processa e organiza os tweets de forma cronológica.
2. **🤖 Postagem automatizada:** Garante que todos os tweets sejam importados para o Bluesky, mesmo em casos de interrupções.
3. **🔄 Controle de duplicidade:** Evita que tweets já postados sejam importados novamente.
4. **🖥️ Interface gráfica moderna:** Oferece uma GUI amigável para facilitar o uso.
5. **⏳ Sistema de retomada:** Salva o progresso da importação para continuidade em caso de falhas ou interrupções.

---

## 🛠️ Requisitos

### Requisitos do Bluesky
- Gere uma chave de aplicativos:
  - Acesse as configurações do Bluesky.
  - Navegue até "Privacidade e Segurança".
  - Crie uma chave de aplicativos.

### Requisitos do Twitter
- Solicite os seus dados no Twitter:
  1. Acesse `Configurações > Sua conta > Baixe um arquivo com seus dados`.
  2. Aguarde o recebimento do arquivo (normalmente dentro de 24 horas).
  3. Verifique seu e-mail e baixe o arquivo dentro do prazo informado.
  4. Extraia o conteúdo do arquivo e localize o arquivo chamado `tweets.js`.

---

## 🚀 Instruções de Uso

1. **Configurações iniciais:**
   - Certifique-se de ter Python instalado.
   - Baixe o código desta aplicação e descompacte-o no seu computador.

2. **Instalação de dependências:**
   Execute o seguinte comando no terminal para instalar as dependências necessárias:
   ```bash
   pip install -r requirements.txt
   ```

3. **Execução da interface gráfica:**
   - Abra sua IDE preferida (por exemplo, VSCode ou PyCharm) e execute o arquivo `bluesky_import_gui.py`.
   - Na interface:
     - Insira seu handle do Bluesky (ex.: `usuario.bsky.social`).
     - Insira sua chave de aplicações do Bluesky.
     - Cole o caminho do arquivo `tweets.js` (clique com o botão direito no arquivo e escolha a opção "Copiar como caminho").

4. **Execução em modo terminal (opcional):**
   - Caso prefira, você pode executar o script diretamente no terminal:
   ```bash
   python script.py
   ```

---

## 🧑‍💻 Detalhes técnicos

### Arquivo `bluesky_import_gui.py`
- **Finalidade:** Fornece uma interface gráfica moderna e intuitiva para o processo de importação.
- **Funcionalidades:**
  - Seleção de arquivo através de um navegador de arquivos.
  - Barra de progresso para visualização em tempo real do status da importação.
  - Controle de interrupções e retomada automática.
- **Tecnologias utilizadas:** Tkinter, threading para operações assíncronas.

### Arquivo `script.py`
- **Finalidade:** Implementa a lógica principal de autenticação, leitura de dados e postagem no Bluesky.
- **Funcionalidades:**
  - Autenticação via API do Bluesky utilizando `atproto`.
  - Verifica duplicidade de postagens para evitar redundância.
  - Ordena tweets cronologicamente para uma importação consistente.
  - Implementa rate limiting adaptativo para evitar bloqueios na API do Bluesky.

### Sistema de backup e retomada
- **Progresso salvo em arquivo:**
  - O progresso da importação é armazenado no arquivo `import_progress.pkl`, garantindo a continuidade após falhas.
  - Tweets já importados são marcados como completados para evitar repetições.

---

## ⚖️ Direitos Autorais e Termos de Uso

Este código é **opensource** e licenciado sob a [GNU General Public License v3 (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.html). Isso significa que:

1. Você pode usar, modificar e redistribuir o código livremente.
2. Modificações ou redistribuições devem manter a mesma licença GPLv3, garantindo que o software e quaisquer derivações permaneçam livres.
3. É obrigatório fornecer créditos ao autor original.
4. Este software é fornecido "como está", sem garantias de qualquer tipo.

### 🛡️ Considerações importantes
- O código não coleta nenhum dado pessoal, nem do arquivo exportado do Twitter nem da sua conta no Bluesky. Todo o processamento é realizado localmente no seu computador.
- O uso do código é de sua responsabilidade, e não nos responsabilizamos por eventuais bloqueios ou suspensões de contas devido às diretrizes de uso das redes sociais.

---

## 🤝 Contribuições
Contribuições são bem-vindas! Para relatar problemas ou sugerir melhorias, utilize a página de "Issues" no repositório do GitHub.

---

## 📞 Suporte
Em caso de dúvidas ou dificuldades, entre em contato através do e-mail fornecido no repositório ou abra uma "Issue" no GitHub.

Agradecemos por utilizar nossa ferramenta. **Boa migração!** 🌟

