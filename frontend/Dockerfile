FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Copy all files
COPY . .

# Next.js telemetry disable
ENV NEXT_TELEMETRY_DISABLED 1

# Start development server
CMD ["npm", "run", "dev"]
