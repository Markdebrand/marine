Next.js app para HSOMarine, empaquetada en Docker y servida con Nginx.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

Backend base URL en el cliente se controla con `NEXT_PUBLIC_API_URL`. En Docker, el Nginx del frontend proxya a `/api` hacia el servicio `backend`.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Docker build (opcional)

Se construye automáticamente desde los stacks de Portainer. Si deseas construir local:

```bash
docker build -f frontend/Dockerfile.frontend --build-arg NEXT_PUBLIC_API_URL=http://localhost:8080/api -t hsomarine-frontend ./frontend
```
