# Use official Bun image as base
FROM oven/bun:latest

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json bun.lockb ./

# Install dependencies
RUN bun install --production

# Install Chromium
RUN apt-get update && \
    apt-get install -y chromium

# Copy source code
COPY src ./src
COPY tsconfig.json ./

# Create necessary directories for Lighthouse
RUN mkdir -p dist/locales

# Copy Lighthouse files
RUN cp -r node_modules/lighthouse/shared/localization/locales/* dist/locales/ && \
    cp -r node_modules/lighthouse/core/lib/* dist/

# Compile TypeScript with target=node
RUN bun build ./src/server.ts --outfile dist/server.js --target=node

# Expose gRPC port
EXPOSE 50053

# Set environment to production
ENV NODE_ENV=production
ENV LIGHTHOUSE_CHROMIUM_PATH=/usr/bin/chromium

# Run the server
CMD ["bun", "run", "dist/server.js"]