# ─── Stage 0: base ───
FROM node:22-alpine AS base
RUN corepack enable && corepack prepare pnpm@9.15.0 --activate
WORKDIR /app

# ─── Stage 1: pruner — turbo prune for health app ───
FROM base AS pruner
RUN npm install -g turbo@^2.5.0
COPY . .
RUN turbo prune @autopilot/health --docker

# ─── Stage 2: installer — install deps ───
FROM base AS installer
# Copy pruned lockfile + package manifests
COPY --from=pruner /app/out/json/ .
COPY --from=pruner /app/out/pnpm-lock.yaml ./pnpm-lock.yaml
COPY --from=pruner /app/out/pnpm-workspace.yaml ./pnpm-workspace.yaml
RUN pnpm install --no-frozen-lockfile

# Copy pruned source + build configs
COPY --from=pruner /app/out/full/ .
# turbo prune may not include root-level config files — copy explicitly
COPY --from=pruner /app/tsconfig.base.json ./tsconfig.base.json
COPY --from=pruner /app/turbo.json ./turbo.json

# Build
ENV DOCKER_BUILD=true
ENV NODE_ENV=production
RUN pnpm turbo build --filter=@autopilot/health

# Ensure optional dirs exist for COPY in runner stage
RUN mkdir -p /app/apps/health/public

# ─── Stage 3: runner ───
FROM node:22-alpine AS runner
WORKDIR /app

RUN addgroup --system nodejs && adduser --system --ingroup nodejs nextjs

# Copy standalone output
COPY --from=installer /app/apps/health/.next/standalone ./
COPY --from=installer /app/apps/health/.next/static ./apps/health/.next/static

# Ensure public dir exists (may be empty)
RUN mkdir -p ./apps/health/public
COPY --from=installer /app/apps/health/public ./apps/health/public

RUN chown -R nextjs:nodejs /app

USER nextjs

ENV NODE_ENV=production
ENV HOSTNAME=0.0.0.0
ENV PORT=4803
EXPOSE 4803

CMD ["node", "apps/health/server.js"]
