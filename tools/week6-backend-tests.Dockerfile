FROM maven:3.9-eclipse-temurin-21-alpine AS tests
WORKDIR /build
COPY pom.xml .
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 mvn -q test
FROM scratch
COPY --from=tests /build/target/surefire-reports/ /
