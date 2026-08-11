# Little Fear Adaptive Framework — Backend

Backend e infraestrutura de dados do **Little Fear Adaptive Framework (LFAF)**, projeto de mestrado voltado ao desenvolvimento de uma arquitetura adaptativa para experiências de exposição em realidade virtual, utilizando dados fisiológicos do usuário.

> **Status:** Em desenvolvimento — versão inicial da infraestrutura

---

## Sobre o projeto

O **Little Fear Adaptive Framework (LFAF)** tem como objetivo investigar uma arquitetura capaz de utilizar informações fisiológicas e comportamentais do usuário para apoiar a adaptação dinâmica de ambientes de realidade virtual durante experiências de exposição.

Nesta etapa do projeto, o foco está na construção da infraestrutura responsável por:

* receber dados fisiológicos provenientes do aplicativo de monitoramento;
* gerenciar sessões experimentais;
* armazenar as medições de frequência cardíaca;
* disponibilizar uma API para comunicação com aplicações externas;
* preparar a infraestrutura para o processamento dos dados por agentes;
* fornecer uma base para futuras integrações com o ambiente de realidade virtual.

A arquitetura está sendo desenvolvida de forma modular para permitir a evolução gradual do sistema.

---

# Arquitetura

A arquitetura inicial do LFAF é composta por diferentes componentes, desenvolvidos separadamente:

```text
┌───────────────────────┐
│   Heart Rate Sensor   │
│        HS500          │
└───────────┬───────────┘
            │
            │ Bluetooth
            ▼
┌───────────────────────┐
│    Flutter App        │
│  Heart Rate Monitor   │
└───────────┬───────────┘
            │
            │ HTTP
            ▼
┌───────────────────────┐
│      Flask API        │
│       LFAF            │
└───────┬─────────┬─────┘
        │         │
        │         │
        ▼         ▼
┌────────────┐ ┌────────────┐
│ PostgreSQL │ │   Redis    │
│            │ │            │
│ Dados      │ │ Mensagens  │
│ persistidos│ │ / agentes  │
└────────────┘ └─────┬──────┘
                     │
                     ▼
              ┌──────────────┐
              │ Multi-Agent  │
              │    System    │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │     Unity    │
              │   VR / Map   │
              └──────────────┘
```

### Estado atual

Nesta primeira etapa, o fluxo implementado é:

```text
Flutter
   │
   │ HTTP
   ▼
Flask
   │
   ▼
PostgreSQL
```

O Redis e a arquitetura multiagente já fazem parte do planejamento do sistema, mas ainda serão implementados nas próximas etapas.

---

# Tecnologias

## Backend

* **Python**
* **Flask**
* **Flask-SQLAlchemy**
* **psycopg**

## Banco de dados

* **PostgreSQL 16**
* **pgAdmin**

## Infraestrutura

* **Docker**
* **Docker Compose**
* **Redis 7**

## Cliente

O aplicativo de monitoramento cardíaco é desenvolvido separadamente em:

* **Flutter**
* **Bluetooth Low Energy (BLE)**
* Sensor cardíaco **HS500**

O aplicativo Flutter **não faz parte deste repositório**.

---

# Estrutura do projeto

```text
backend/
│
├── app/
│   ├── __init__.py
│   └── extensions.py
│
├── agents/
│
├── config/
│   └── config.py
│
├── gateway/
│
├── models/
│   ├── __init__.py
│   ├── user.py
│   ├── phobia.py
│   ├── session.py
│   └── heart_rate.py
│
├── routes/
│   ├── __init__.py
│   ├── health.py
│   ├── sessions.py
│   └── heart_rates.py
│
├── services/
│   ├── __init__.py
│   ├── session_service.py
│   └── heart_rate_service.py
│
├── .env
├── requirements.txt
└── run.py
```

---

# Modelo de dados

A primeira versão do banco possui quatro entidades principais:

```text
Phobia
   │
   │ 1:N
   ▼
User
   │
   │ 1:N
   ▼
Session
   │
   │ 1:N
   ▼
HeartRate
```

## `phobias`

Armazena as fobias consideradas pelo sistema.

| Campo  | Tipo    | Descrição     |
| ------ | ------- | ------------- |
| `id`   | Integer | Identificador |
| `name` | String  | Nome da fobia |

Exemplos:

```text
1 → Aracnofobia
2 → Acrofobia
```

---

## `users`

Representa os participantes do experimento.

Cada registro de usuário está associado a uma fobia específica.

| Campo       | Tipo    | Descrição            |
| ----------- | ------- | -------------------- |
| `id`        | Integer | Identificador        |
| `name`      | String  | Nome do participante |
| `age`       | Integer | Idade                |
| `phobia_id` | Integer | Fobia associada      |

A decisão de associar a fobia ao usuário foi tomada considerando o desenho experimental atual: caso o mesmo participante participe de experimentos relacionados a outra fobia, será utilizado outro registro de participante.

---

## `sessions`

Representa uma execução/teste do ambiente de realidade virtual.

> **Uma sessão corresponde a uma execução de um mapa por um participante.**

| Campo        | Tipo     | Descrição        |
| ------------ | -------- | ---------------- |
| `id`         | Integer  | Identificador    |
| `user_id`    | Integer  | Participante     |
| `map_name`   | String   | Mapa executado   |
| `started_at` | DateTime | Início da sessão |
| `ended_at`   | DateTime | Fim da sessão    |

Exemplo:

```text
Session #15
├── User: 1
├── Phobia: Aracnofobia
├── Map: spider_room_01
├── Started: 14:30:00
└── Ended: 14:42:37
```

---

## `heart_rates`

Armazena as medições fisiológicas coletadas durante uma sessão.

| Campo        | Tipo     | Descrição           |
| ------------ | -------- | ------------------- |
| `id`         | Integer  | Identificador       |
| `session_id` | Integer  | Sessão associada    |
| `bpm`        | Float    | Frequência cardíaca |
| `timestamp`  | DateTime | Momento da medição  |

Cada medição é armazenada individualmente:

```text
Session 15

14:30:01 → 82 BPM
14:30:02 → 83 BPM
14:30:03 → 84 BPM
14:30:04 → 86 BPM
14:30:05 → 89 BPM
```

Isso permite reconstruir posteriormente toda a evolução fisiológica do participante durante uma sessão.

---

# Comunicação com o aplicativo

O aplicativo Flutter recebe continuamente as medições do sensor cardíaco.

Para reduzir a quantidade de requisições HTTP, as medições são agrupadas em pequenos lotes.

Inicialmente, será utilizado um **buffer de 5 medições**:

```text
HS500
 │
 ├── 82 BPM
 ├── 83 BPM
 ├── 84 BPM
 ├── 86 BPM
 └── 89 BPM
        │
        ▼
   Buffer = 5
        │
        ▼
     Flask API
```

O servidor recebe o lote, mas persiste cada medição individualmente no PostgreSQL.

### Exemplo de requisição

```http
POST /sessions/15/heart-rate
```

```json
{
  "measurements": [
    {
      "bpm": 82,
      "timestamp": "2026-08-11T16:00:01"
    },
    {
      "bpm": 83,
      "timestamp": "2026-08-11T16:00:02"
    },
    {
      "bpm": 84,
      "timestamp": "2026-08-11T16:00:03"
    },
    {
      "bpm": 86,
      "timestamp": "2026-08-11T16:00:04"
    },
    {
      "bpm": 89,
      "timestamp": "2026-08-11T16:00:05"
    }
  ]
}
```

Resposta:

```json
{
  "status": "ok",
  "session_id": 15,
  "received": 5
}
```

---

# API

## Health Check

Verifica o funcionamento da API e a conexão com o banco.

```http
GET /health
```

Resposta:

```json
{
  "status": "ok",
  "project": "LFAF",
  "version": "0.3",
  "database": "connected"
}
```

---

## Criar sessão

Inicia uma nova execução de um mapa.

```http
POST /sessions
```

Body:

```json
{
  "user_id": 1,
  "map_name": "spider_room_01"
}
```

---

## Consultar sessão

```http
GET /sessions/{session_id}
```

---

## Enviar frequência cardíaca

```http
POST /sessions/{session_id}/heart-rate
```

Recebe um lote de medições.

---

## Encerrar sessão

```http
POST /sessions/{session_id}/finish
```

Ao finalizar uma sessão, o campo `ended_at` é preenchido e novas medições não devem ser aceitas para aquela sessão.

---

# Execução local

## Pré-requisitos

É necessário possuir:

* Python 3.12+
* Docker
* Docker Compose
* PostgreSQL/pgAdmin opcionalmente para administração
* Git

---

## 1. Clonar o projeto

```bash
git clone <repository-url>
cd MSC_LFAF
```

---

## 2. Criar ambiente virtual

Dentro do backend:

```bash
cd backend
python3 -m venv venv
```

Ativar:

```bash
source venv/bin/activate
```

---

## 3. Instalar dependências

```bash
pip install -r requirements.txt
```

---

## 4. Configurar variáveis de ambiente

Criar `backend/.env`:

```env
FLASK_ENV=development
FLASK_DEBUG=true

HOST=0.0.0.0
PORT=5000

DATABASE_URL=postgresql+psycopg://lfaf_user:password@localhost:5432/lfaf
```

> **Não versionar o arquivo `.env`.**

---

# Banco de dados

O PostgreSQL é executado através do Docker.

Exemplo de configuração:

```text
PostgreSQL 16
    │
    └── Port: 5432

Redis 7
    │
    └── Port: 6379
```

Para iniciar os containers:

```bash
docker compose up -d
```

Verificar:

```bash
docker ps
```

Para parar:

```bash
docker compose down
```

---

# Executar o backend

Com o ambiente virtual ativado:

```bash
python run.py
```

O servidor estará disponível em:

```text
http://localhost:5000
```

Teste:

```bash
curl http://localhost:5000/health
```

---

# Fluxo experimental

O fluxo previsto para uma sessão experimental é:

```text
1. Participante selecionado
        │
        ▼
2. Início da sessão
        │
        ▼
3. Aplicativo conecta ao HS500
        │
        ▼
4. Participante inicia o mapa
        │
        ▼
5. Coleta contínua de HR
        │
        ▼
6. Buffer de 5 medições
        │
        ▼
7. Envio para Flask
        │
        ├───────────────┐
        ▼               ▼
   PostgreSQL       Processamento
        │             futuro
        │
        ▼
8. Continuação da sessão
        │
        ▼
9. Finalização do mapa
        │
        ▼
10. Encerramento da sessão
```

---

# Evolução planejada

A infraestrutura atual representa apenas a primeira camada do LFAF.

As próximas etapas incluem:

### Processamento fisiológico

Implementação de componentes responsáveis por analisar os dados recebidos:

```text
Heart Rate
    ↓
Monitoring Agent
    ↓
Physiological State
```

### Arquitetura multiagente

Posteriormente, os dados fisiológicos serão utilizados por agentes especializados:

```text
              Heart Rate
                   │
                   ▼
          ┌─────────────────┐
          │ MonitoringAgent │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │  EmotionAgent   │
          └────────┬────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ AdaptationAgent │
          └────────┬────────┘
                   │
                   ▼
             Adaptation
```

### Comunicação em tempo real

O Redis será utilizado futuramente para comunicação entre componentes e agentes, permitindo o processamento dos dados sem depender diretamente do banco como mecanismo de comunicação.

### Integração com Unity

As decisões produzidas pelos agentes serão posteriormente encaminhadas para o ambiente de realidade virtual:

```text
Physiological Data
        ↓
      Agents
        ↓
Adaptation Decision
        ↓
Environment Gateway
        ↓
      Unity VR
```

### Eventos e adaptações

Também estão previstas futuras entidades para registrar:

* eventos ocorridos no ambiente;
* mudanças de estado;
* decisões dos agentes;
* adaptações realizadas;
* relação temporal entre estímulos, respostas fisiológicas e adaptações.

---

# Princípios da arquitetura

O desenvolvimento do backend segue alguns princípios:

### Separação de responsabilidades

A API, regras de negócio, persistência e agentes são mantidos em componentes separados.

```text
Routes
   ↓
Services
   ↓
Models / Database
```

### Dados fisiológicos como dados observados

Os valores de BPM são armazenados como dados brutos.

Interpretações como:

```text
baixo estresse
estresse elevado
recuperação
```

serão responsabilidades de componentes de processamento/agentes, e não propriedades do dado bruto.

### Sessões como unidade experimental

Toda coleta fisiológica está associada a uma sessão, permitindo posteriormente reconstruir e analisar uma experiência completa.

### Evolução incremental

A arquitetura será implementada gradualmente:

```text
v0.1 → Infraestrutura Docker
v0.2 → Flask API
v0.3 → PostgreSQL
v0.4 → Sessões + Heart Rate
v0.5 → Integração Flutter
v0.6 → Redis
v0.7 → Agentes
...
```

As versões podem ser alteradas conforme a evolução do projeto.

---

# Status atual

### Implementado

* [x] PostgreSQL em Docker
* [x] Redis em Docker
* [x] Backend Flask
* [x] Ambiente virtual Python
* [x] Configuração via `.env`
* [x] SQLAlchemy
* [x] Modelo de usuários
* [x] Modelo de fobias
* [x] Modelo de sessões
* [x] Modelo de frequência cardíaca
* [x] Health check
* [x] Criação de sessões
* [x] Consulta de sessões
* [x] Recebimento de lotes de HR
* [x] Persistência individual das medições
* [x] Encerramento de sessões
* [x] Bloqueio de novas medições após encerramento

### Em desenvolvimento

* [ ] Integração com aplicativo Flutter
* [ ] Buffer de 5 medições no cliente
* [ ] Comunicação Flutter → Flask
* [ ] Exportação/integração dos dados experimentais

### Planejado

* [ ] Redis Pub/Sub
* [ ] MonitoringAgent
* [ ] Processamento fisiológico
* [ ] EmotionAgent
* [ ] AdaptationAgent
* [ ] Gateway de comunicação com Unity
* [ ] Eventos da simulação
* [ ] Registro das adaptações
* [ ] Integração completa com o ambiente VR

---

# Projeto de Mestrado

O LFAF está sendo desenvolvido como parte de uma pesquisa de **Mestrado em Modelagem Computacional**, com foco na aplicação de sistemas multiagentes e dados fisiológicos para apoiar a adaptação de experiências de exposição em realidade virtual.

O backend deste repositório constitui a infraestrutura responsável pela comunicação, gerenciamento das sessões experimentais e persistência dos dados utilizados pelo framework.
