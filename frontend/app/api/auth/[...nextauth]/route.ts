import NextAuth from "next-auth"
import GithubProvider from "next-auth/providers/github"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"

const handler = NextAuth({
    providers: [
        GithubProvider({
            clientId: process.env.GITHUB_ID ?? "",
            clientSecret: process.env.GITHUB_SECRET ?? "",
        }),
        GoogleProvider({
            clientId: process.env.GOOGLE_CLIENT_ID ?? "",
            clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
        }),
        // 模拟登录 Provider (用于无需配置 .env 的本地体验)
        CredentialsProvider({
            name: "DevLogin",
            credentials: {
                email: { label: "Email", type: "text", placeholder: "demo@example.com" }
            },
            async authorize(credentials, req) {
                // 只要输入了邮箱，就允许登录
                if (credentials?.email) {
                    return { id: credentials.email, name: credentials.email.split("@")[0], email: credentials.email }
                }
                return null
            }
        })
    ],
    session: {
        strategy: "jwt",
    },
    callbacks: {
        async jwt({ token, account, profile, user }) {
            // When user first signs in
            if (account && profile) {
                console.log("JWT Callback - Provider:", account.provider);
                console.log("JWT Callback - Profile:", profile);

                // GitHub specific handling
                if (account.provider === "github") {
                    token.login = (profile as any).login;
                    token.email = token.email || (profile as any).email;
                    token.name = token.name || (profile as any).name || (profile as any).login;
                    console.log("JWT Callback - GitHub login:", token.login);
                }
            }
            return token;
        },
        async session({ session, token }) {
            console.log("Session Callback - Token:", token);

            // Add all relevant fields to session
            if (session.user) {
                if (token.login) {
                    (session.user as any).login = token.login;
                }
                if (token.email) {
                    session.user.email = token.email as string;
                }
                if (token.name) {
                    session.user.name = token.name as string;
                }

                console.log("Session Callback - Final session.user:", session.user);
            }
            return session;
        }
    },
    // 必须配置 secret 才能在生产环境运行，开发环境 NextAuth 会自动处理警告，但在 production 会报错
    secret: process.env.NEXTAUTH_SECRET || "dev-secret-123",
})

export { handler as GET, handler as POST }
