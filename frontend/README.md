# Frontend Gastor

Interface moderna para a plataforma Gastor, construída com Next.js 14 (App Router).

## Stack

- **Framework**: Next.js 14
- **Estilização**: Tailwind CSS
- **Gráficos**: Recharts
- **Estado**: Context API (AuthContext)
- **Autenticação**: Google OAuth + JWT

## Páginas Principais
- `/login`: Acesso ao sistema
- `/register`: Criação de conta
- `/trading`: Dashboard principal


## Setup

Certifique-se de que o **Backend** está rodando na porta `8000`.

```bash
# 1. Instalar dependências
npm install

# 2. Rodar versão de desenvolvimento
npm run dev
```

Acesse `http://localhost:3000`.

## Configuração

O frontend se comunica com a API via `src/lib/api.ts`.
Por padrão, assume proxy para `http://localhost:8000`.
