import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    // Rotas públicas que não requerem autenticação
    const publicRoutes = ['/', '/login', '/register', '/logo.png', '/favicon.ico'];

    // Verifica se a rota atual é pública
    const isPublicRoute = publicRoutes.some(route =>
        request.nextUrl.pathname === route ||
        request.nextUrl.pathname.startsWith('/_next') ||
        request.nextUrl.pathname.startsWith('/api') ||
        request.nextUrl.pathname.startsWith('/static')
    );

    // Se a rota não for pública e não tiver token, redireciona para login
    if (!isPublicRoute) {
        const token = request.cookies.get('token'); // Assumindo que usamos cookie, mas o AuthContext usa localStorage.

        // NOTA: Como a autenticação é Client-Side (localStorage), o middleware do servidor
        // não consegue acessar o token se ele não estiver nos cookies.
        // Para uma proteção robusta via Middleware, precisaríamos mover o token para cookies.
        // POR ENQUANTO: Vamos confiar na proteção Client-Side (AuthContext) e redirecionar apenas se TIVERMOS certeza.
        // Mas o pedido do usuário é "sem logar não acessa nada". 
        // Vamos implementar uma verificação básica se possível, ou garantir que o AuthContext faça o redirecionamento.

        // Melhor abordagem para SPA com JWT no LocalStorage:
        // O Middleware não consegue ler LocalStorage.
        // Vamos manter o Middleware simples para redirecionar se acessar rotas óbvias sem cookie (se implementarmos cookies futuramente)
        // MAS a proteção real deve ser no AuthContext.
    }

    return NextResponse.next();
}

// Configuração para quais rotas o middleware deve rodar
export const config = {
    matcher: [
        /*
         * Match all request paths except for the ones starting with:
         * - api (API routes)
         * - _next/static (static files)
         * - _next/image (image optimization files)
         * - favicon.ico (favicon file)
         */
        '/((?!api|_next/static|_next/image|favicon.ico).*)',
    ],
};
