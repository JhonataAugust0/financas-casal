# 🌱 Gestão Financeira para Casais

Uma aplicação web *mobile-first* de gestão financeira para casais, desenvolvida com **Python**, **Streamlit** e **Arquitetura Hexagonal (Ports & Adapters)**, seguindo rigorosamente os princípios **SOLID**.

---

## 🏛️ Arquitetura Hexagonal & Princípios SOLID

```
src/
├── domain/                          ← Regras de negócio puras (0 dependências de framework)
│   ├── models.py                    ← Dataclasses (User, Expense, Goal, JointSimulationResult)
│   └── financial_calculator.py      ← FinancialCalculator (serviço de domínio puro)
├── ports/                           ← Contratos e Interfaces Abstratas (ABC)
│   └── repository.py               ← FinancialRepository (Porta de Persistência)
├── adapters/                        ← Implementações de Infraestrutura
│   ├── sqlite_repository.py        ← Adapter SQLite (dev/test local)
│   └── supabase_repository.py      ← Adapter Supabase REST API (produção)
└── ui/                              ← Apresentação e Orquestração Streamlit
    ├── main.py                      ← Entrypoint com Injeção de Dependência
    ├── styles.py                    ← CSS isolado
    ├── components/
    │   └── charts.py               ← Geradores de gráficos Altair (funções puras)
    └── tabs/
        ├── resumo.py               ← 📊 Resumo (Custo de vida + Uso da Mesada)
        ├── orcamento.py            ← 💰 Orçamento (Entradas, Mesada e Despesas)
        ├── metas.py                ← 🎯 Metas (Algoritmo de Cascata & Travas de Segurança)
        └── simulador.py            ← ⚖️ Simulador de Junção de Rendas (Déficit Oculto)
```

### Princípios SOLID Aplicados:
* **Single Responsibility Principle (SRP)**: Cada módulo possui uma única responsabilidade. O `FinancialCalculator` executa apenas matemática financeira, os gráficos Altair em `charts.py` geram apenas objetos visuais sem chamadas `st.*`, e a UI é dividida em abas focadas.
* **Open/Closed Principle (OCP)**: Novos adaptadores de banco de dados (ex: Postgres direto, DynamoDB) podem ser adicionados criando uma classe derivada de `FinancialRepository` sem modificar o código do domínio ou da interface gráfica.
* **Liskov Substitution Principle (LSP)**: `SQLiteRepository` e `SupabaseRepository` cumprem a mesma interface abstrata e podem ser substituídos de forma transparente.
* **Interface Segregation Principle (ISP)**: A interface `FinancialRepository` expõe métodos coesos e bem definidos para usuários, despesas e metas.
* **Dependency Inversion Principle (DIP)**: As abas e a orquestração dependem da abstração `FinancialRepository`, e a instância concreta é injetada dinamicamente via Factory Pattern em `main.py`.

---

## 💡 Regras de Negócio & Motor Financeiro

### 1. 🏠 "O NOSSO" (Bolo Central da Família) vs 👤 "O MEU / O SEU" (Mesada Individual)
- **O NOSSO**: Moradia, contas básicas, mercado, feira, ração/areia dos gatos, **Saúde Física e Mental** (Terapia, remédios, psiquiatra) e **Higiene Básica**. Entra no **Custo de Vida**, na **Reserva de Paz** e no **Simulador de Junção**.
- **O MEU / O SEU**: Cosméticos, vaidade, skincare, hobbies, iFood desejo individual. **NÃO infla o Custo de Vida** do Bolo Central; é abatido diretamente da **Mesada Individual (R$ 500,00)** de cada um.

### 2. 🛡️ Reserva de Paz (Sobrevivência vs Manutenção)
- **Modo Sobrevivência**: Garante o pagamento apenas do custo fixo essencial (🏠 O NOSSO).
- **Modo Manutenção**: O alvo da reserva expande dinamicamente para cobrir os boletos básicos + a mesada individual de cada parceiro.

### 3. 🚀 Algoritmo de Alocação em Cascata
- Distribui o valor total do aporte conjunto nas metas seguindo estritamente a prioridade definida.
- A **Reserva de Paz** é travada obrigatoriamente na **Prioridade 1** e preenchida integralmente antes de liberar recursos para as demais metas.

### 4. ⚖️ Simulador de Junção de Rendas (Déficit Oculto)
- Detecta matematicamente o "Déficit Oculto": cenários em que o modelo de contas separadas força um dos parceiros a ficar no vermelho ao pagar suas contas básicas e tentar retirar a mesada.

---

## 🚀 Instalação e Execução Local

### Pré-requisitos
* Python 3.11+
* [Poetry](https://python-poetry.org/)

### Passos:
1. Clone o repositório e instale as dependências:
   ```bash
   poetry install
   ```

2. Execute em ambiente de desenvolvimento local (SQLite):
   ```bash
   poetry run streamlit run src/ui/main.py
   ```


