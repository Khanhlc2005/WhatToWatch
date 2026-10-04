# Giai đoạn 1: Build mã nguồn bằng Maven
FROM maven:3.9-eclipse-temurin-21-alpine AS builder
WORKDIR /build

COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

# Tìm chính xác file executable jar của Spring Boot và đổi tên thành app.jar
RUN find target/ -name "*.jar" ! -name "original-*.jar" -exec mv {} target/app.jar \;

# Giai đoạn 2: Runtime JRE 21 siêu nhẹ
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app

COPY --from=builder /build/target/app.jar app.jar

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]