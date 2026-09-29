# ==========================================
# GIAI ĐOẠN 1: Môi trường Maven 3.9 + JDK 21 để build mã nguồn
# ==========================================
FROM maven:3.9-eclipse-temurin-21-alpine AS builder

WORKDIR /build

# Copy file pom.xml vào trước
COPY pom.xml .

# Copy toàn bộ thư mục mã nguồn src (bao gồm controller, entity, mapper, dto...)
COPY src ./src

# Biên dịch mã nguồn, chạy MapStruct/Lombok processor và đóng gói file JAR
RUN mvn clean package -DskipTests

# ==========================================
# GIAI ĐOẠN 2: Môi trường JRE 21 siêu nhẹ để chạy ứng dụng
# ==========================================
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Lấy trực tiếp file .jar đã build xong từ GIAI ĐOẠN 1
COPY --from=builder /build/target/*.jar app.jar

# Mở cổng 8080 của ứng dụng
EXPOSE 8080

# Chạy file jar
ENTRYPOINT ["java", "-jar", "app.jar"]