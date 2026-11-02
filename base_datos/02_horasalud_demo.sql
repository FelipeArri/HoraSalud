-- =====================================================================
-- HoraSalud - Base de datos de demostracion (SOLO DATOS FICTICIOS)
-- Contiene: tablas creadas por Django (migrate) + datos de cargar_datos_demo.
-- RUT ficticios desde 30.000.001; ningun usuario puede iniciar sesion
-- y no hay superusuario: cada integrante crea el suyo (createsuperuser).
-- Requiere antes: 01_crear_base_y_usuario.sql
-- Importar en phpMyAdmin: pestana "Importar" -> este archivo -> Continuar.
-- =====================================================================
USE horasalud_db;

-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: horasalud_db
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `agendaapp_agenda`
--

DROP TABLE IF EXISTS `agendaapp_agenda`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agendaapp_agenda` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `especialidad_id` bigint(20) NOT NULL,
  `profesional_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `agendaApp_agenda_profesional_id_34cdabfd_fk_autentica` (`profesional_id`),
  KEY `agendaApp_a_especia_4db1ab_idx` (`especialidad_id`,`fecha`),
  CONSTRAINT `agendaApp_agenda_especialidad_id_d5015db8_fk_agendaApp` FOREIGN KEY (`especialidad_id`) REFERENCES `agendaapp_especialidad` (`id`),
  CONSTRAINT `agendaApp_agenda_profesional_id_34cdabfd_fk_autentica` FOREIGN KEY (`profesional_id`) REFERENCES `autenticacionapp_profesional` (`usuario_id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agendaapp_agenda`
--

LOCK TABLES `agendaapp_agenda` WRITE;
/*!40000 ALTER TABLE `agendaapp_agenda` DISABLE KEYS */;
INSERT INTO `agendaapp_agenda` VALUES (1,'2026-11-02',1,'2d3b2d08c6324492af4e76185f16fe49'),(2,'2026-11-02',2,'e9ccb03123cd4587b05b549a12811b35'),(3,'2026-11-02',3,'94d9e05dd1944957bc3f62b88f161a34'),(4,'2026-11-03',1,'2d3b2d08c6324492af4e76185f16fe49'),(5,'2026-11-03',2,'e9ccb03123cd4587b05b549a12811b35'),(6,'2026-11-03',3,'94d9e05dd1944957bc3f62b88f161a34'),(7,'2026-11-04',1,'2d3b2d08c6324492af4e76185f16fe49'),(8,'2026-11-04',2,'e9ccb03123cd4587b05b549a12811b35'),(9,'2026-11-04',3,'94d9e05dd1944957bc3f62b88f161a34'),(10,'2026-11-05',1,'2d3b2d08c6324492af4e76185f16fe49'),(11,'2026-11-05',2,'e9ccb03123cd4587b05b549a12811b35'),(12,'2026-11-05',3,'94d9e05dd1944957bc3f62b88f161a34'),(13,'2026-11-06',1,'2d3b2d08c6324492af4e76185f16fe49'),(14,'2026-11-06',2,'e9ccb03123cd4587b05b549a12811b35'),(15,'2026-11-06',3,'94d9e05dd1944957bc3f62b88f161a34');
/*!40000 ALTER TABLE `agendaapp_agenda` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agendaapp_bloquehorario`
--

DROP TABLE IF EXISTS `agendaapp_bloquehorario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agendaapp_bloquehorario` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `hora_inicio` time(6) NOT NULL,
  `hora_fin` time(6) NOT NULL,
  `estado` varchar(12) NOT NULL,
  `agenda_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_bloque_agenda_horario` (`agenda_id`,`hora_inicio`),
  CONSTRAINT `agendaApp_bloquehora_agenda_id_97212c10_fk_agendaApp` FOREIGN KEY (`agenda_id`) REFERENCES `agendaapp_agenda` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=181 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agendaapp_bloquehorario`
--

LOCK TABLES `agendaapp_bloquehorario` WRITE;
/*!40000 ALTER TABLE `agendaapp_bloquehorario` DISABLE KEYS */;
INSERT INTO `agendaapp_bloquehorario` VALUES (1,'08:00:00.000000','08:20:00.000000','disponible',1),(2,'08:20:00.000000','08:40:00.000000','disponible',1),(3,'08:40:00.000000','09:00:00.000000','disponible',1),(4,'09:00:00.000000','09:20:00.000000','disponible',1),(5,'09:20:00.000000','09:40:00.000000','disponible',1),(6,'09:40:00.000000','10:00:00.000000','disponible',1),(7,'10:00:00.000000','10:20:00.000000','disponible',1),(8,'10:20:00.000000','10:40:00.000000','disponible',1),(9,'10:40:00.000000','11:00:00.000000','disponible',1),(10,'11:00:00.000000','11:20:00.000000','disponible',1),(11,'11:20:00.000000','11:40:00.000000','disponible',1),(12,'11:40:00.000000','12:00:00.000000','disponible',1),(13,'08:00:00.000000','08:20:00.000000','reservado',2),(14,'08:20:00.000000','08:40:00.000000','disponible',2),(15,'08:40:00.000000','09:00:00.000000','disponible',2),(16,'09:00:00.000000','09:20:00.000000','reservado',2),(17,'09:20:00.000000','09:40:00.000000','disponible',2),(18,'09:40:00.000000','10:00:00.000000','disponible',2),(19,'10:00:00.000000','10:20:00.000000','disponible',2),(20,'10:20:00.000000','10:40:00.000000','reservado',2),(21,'10:40:00.000000','11:00:00.000000','disponible',2),(22,'11:00:00.000000','11:20:00.000000','disponible',2),(23,'11:20:00.000000','11:40:00.000000','disponible',2),(24,'11:40:00.000000','12:00:00.000000','disponible',2),(25,'08:00:00.000000','08:20:00.000000','disponible',3),(26,'08:20:00.000000','08:40:00.000000','disponible',3),(27,'08:40:00.000000','09:00:00.000000','reservado',3),(28,'09:00:00.000000','09:20:00.000000','disponible',3),(29,'09:20:00.000000','09:40:00.000000','disponible',3),(30,'09:40:00.000000','10:00:00.000000','disponible',3),(31,'10:00:00.000000','10:20:00.000000','disponible',3),(32,'10:20:00.000000','10:40:00.000000','disponible',3),(33,'10:40:00.000000','11:00:00.000000','disponible',3),(34,'11:00:00.000000','11:20:00.000000','disponible',3),(35,'11:20:00.000000','11:40:00.000000','disponible',3),(36,'11:40:00.000000','12:00:00.000000','disponible',3),(37,'08:00:00.000000','08:20:00.000000','disponible',4),(38,'08:20:00.000000','08:40:00.000000','disponible',4),(39,'08:40:00.000000','09:00:00.000000','reservado',4),(40,'09:00:00.000000','09:20:00.000000','disponible',4),(41,'09:20:00.000000','09:40:00.000000','disponible',4),(42,'09:40:00.000000','10:00:00.000000','disponible',4),(43,'10:00:00.000000','10:20:00.000000','disponible',4),(44,'10:20:00.000000','10:40:00.000000','disponible',4),(45,'10:40:00.000000','11:00:00.000000','disponible',4),(46,'11:00:00.000000','11:20:00.000000','disponible',4),(47,'11:20:00.000000','11:40:00.000000','disponible',4),(48,'11:40:00.000000','12:00:00.000000','disponible',4),(49,'08:00:00.000000','08:20:00.000000','disponible',5),(50,'08:20:00.000000','08:40:00.000000','disponible',5),(51,'08:40:00.000000','09:00:00.000000','disponible',5),(52,'09:00:00.000000','09:20:00.000000','disponible',5),(53,'09:20:00.000000','09:40:00.000000','disponible',5),(54,'09:40:00.000000','10:00:00.000000','disponible',5),(55,'10:00:00.000000','10:20:00.000000','disponible',5),(56,'10:20:00.000000','10:40:00.000000','disponible',5),(57,'10:40:00.000000','11:00:00.000000','disponible',5),(58,'11:00:00.000000','11:20:00.000000','disponible',5),(59,'11:20:00.000000','11:40:00.000000','disponible',5),(60,'11:40:00.000000','12:00:00.000000','reservado',5),(61,'08:00:00.000000','08:20:00.000000','disponible',6),(62,'08:20:00.000000','08:40:00.000000','disponible',6),(63,'08:40:00.000000','09:00:00.000000','disponible',6),(64,'09:00:00.000000','09:20:00.000000','disponible',6),(65,'09:20:00.000000','09:40:00.000000','disponible',6),(66,'09:40:00.000000','10:00:00.000000','disponible',6),(67,'10:00:00.000000','10:20:00.000000','disponible',6),(68,'10:20:00.000000','10:40:00.000000','disponible',6),(69,'10:40:00.000000','11:00:00.000000','disponible',6),(70,'11:00:00.000000','11:20:00.000000','disponible',6),(71,'11:20:00.000000','11:40:00.000000','disponible',6),(72,'11:40:00.000000','12:00:00.000000','disponible',6),(73,'08:00:00.000000','08:20:00.000000','disponible',7),(74,'08:20:00.000000','08:40:00.000000','disponible',7),(75,'08:40:00.000000','09:00:00.000000','disponible',7),(76,'09:00:00.000000','09:20:00.000000','disponible',7),(77,'09:20:00.000000','09:40:00.000000','disponible',7),(78,'09:40:00.000000','10:00:00.000000','disponible',7),(79,'10:00:00.000000','10:20:00.000000','disponible',7),(80,'10:20:00.000000','10:40:00.000000','disponible',7),(81,'10:40:00.000000','11:00:00.000000','disponible',7),(82,'11:00:00.000000','11:20:00.000000','disponible',7),(83,'11:20:00.000000','11:40:00.000000','reservado',7),(84,'11:40:00.000000','12:00:00.000000','disponible',7),(85,'08:00:00.000000','08:20:00.000000','disponible',8),(86,'08:20:00.000000','08:40:00.000000','disponible',8),(87,'08:40:00.000000','09:00:00.000000','disponible',8),(88,'09:00:00.000000','09:20:00.000000','disponible',8),(89,'09:20:00.000000','09:40:00.000000','disponible',8),(90,'09:40:00.000000','10:00:00.000000','disponible',8),(91,'10:00:00.000000','10:20:00.000000','disponible',8),(92,'10:20:00.000000','10:40:00.000000','disponible',8),(93,'10:40:00.000000','11:00:00.000000','disponible',8),(94,'11:00:00.000000','11:20:00.000000','disponible',8),(95,'11:20:00.000000','11:40:00.000000','disponible',8),(96,'11:40:00.000000','12:00:00.000000','disponible',8),(97,'08:00:00.000000','08:20:00.000000','disponible',9),(98,'08:20:00.000000','08:40:00.000000','disponible',9),(99,'08:40:00.000000','09:00:00.000000','reservado',9),(100,'09:00:00.000000','09:20:00.000000','disponible',9),(101,'09:20:00.000000','09:40:00.000000','disponible',9),(102,'09:40:00.000000','10:00:00.000000','disponible',9),(103,'10:00:00.000000','10:20:00.000000','disponible',9),(104,'10:20:00.000000','10:40:00.000000','reservado',9),(105,'10:40:00.000000','11:00:00.000000','disponible',9),(106,'11:00:00.000000','11:20:00.000000','disponible',9),(107,'11:20:00.000000','11:40:00.000000','disponible',9),(108,'11:40:00.000000','12:00:00.000000','disponible',9),(109,'08:00:00.000000','08:20:00.000000','disponible',10),(110,'08:20:00.000000','08:40:00.000000','disponible',10),(111,'08:40:00.000000','09:00:00.000000','disponible',10),(112,'09:00:00.000000','09:20:00.000000','disponible',10),(113,'09:20:00.000000','09:40:00.000000','disponible',10),(114,'09:40:00.000000','10:00:00.000000','disponible',10),(115,'10:00:00.000000','10:20:00.000000','disponible',10),(116,'10:20:00.000000','10:40:00.000000','disponible',10),(117,'10:40:00.000000','11:00:00.000000','disponible',10),(118,'11:00:00.000000','11:20:00.000000','disponible',10),(119,'11:20:00.000000','11:40:00.000000','disponible',10),(120,'11:40:00.000000','12:00:00.000000','disponible',10),(121,'08:00:00.000000','08:20:00.000000','disponible',11),(122,'08:20:00.000000','08:40:00.000000','disponible',11),(123,'08:40:00.000000','09:00:00.000000','disponible',11),(124,'09:00:00.000000','09:20:00.000000','disponible',11),(125,'09:20:00.000000','09:40:00.000000','disponible',11),(126,'09:40:00.000000','10:00:00.000000','disponible',11),(127,'10:00:00.000000','10:20:00.000000','disponible',11),(128,'10:20:00.000000','10:40:00.000000','disponible',11),(129,'10:40:00.000000','11:00:00.000000','disponible',11),(130,'11:00:00.000000','11:20:00.000000','disponible',11),(131,'11:20:00.000000','11:40:00.000000','disponible',11),(132,'11:40:00.000000','12:00:00.000000','disponible',11),(133,'08:00:00.000000','08:20:00.000000','disponible',12),(134,'08:20:00.000000','08:40:00.000000','disponible',12),(135,'08:40:00.000000','09:00:00.000000','disponible',12),(136,'09:00:00.000000','09:20:00.000000','disponible',12),(137,'09:20:00.000000','09:40:00.000000','disponible',12),(138,'09:40:00.000000','10:00:00.000000','reservado',12),(139,'10:00:00.000000','10:20:00.000000','disponible',12),(140,'10:20:00.000000','10:40:00.000000','disponible',12),(141,'10:40:00.000000','11:00:00.000000','disponible',12),(142,'11:00:00.000000','11:20:00.000000','disponible',12),(143,'11:20:00.000000','11:40:00.000000','reservado',12),(144,'11:40:00.000000','12:00:00.000000','disponible',12),(145,'08:00:00.000000','08:20:00.000000','disponible',13),(146,'08:20:00.000000','08:40:00.000000','disponible',13),(147,'08:40:00.000000','09:00:00.000000','disponible',13),(148,'09:00:00.000000','09:20:00.000000','disponible',13),(149,'09:20:00.000000','09:40:00.000000','disponible',13),(150,'09:40:00.000000','10:00:00.000000','disponible',13),(151,'10:00:00.000000','10:20:00.000000','disponible',13),(152,'10:20:00.000000','10:40:00.000000','disponible',13),(153,'10:40:00.000000','11:00:00.000000','disponible',13),(154,'11:00:00.000000','11:20:00.000000','disponible',13),(155,'11:20:00.000000','11:40:00.000000','disponible',13),(156,'11:40:00.000000','12:00:00.000000','disponible',13),(157,'08:00:00.000000','08:20:00.000000','disponible',14),(158,'08:20:00.000000','08:40:00.000000','reservado',14),(159,'08:40:00.000000','09:00:00.000000','disponible',14),(160,'09:00:00.000000','09:20:00.000000','disponible',14),(161,'09:20:00.000000','09:40:00.000000','disponible',14),(162,'09:40:00.000000','10:00:00.000000','disponible',14),(163,'10:00:00.000000','10:20:00.000000','disponible',14),(164,'10:20:00.000000','10:40:00.000000','disponible',14),(165,'10:40:00.000000','11:00:00.000000','disponible',14),(166,'11:00:00.000000','11:20:00.000000','disponible',14),(167,'11:20:00.000000','11:40:00.000000','disponible',14),(168,'11:40:00.000000','12:00:00.000000','disponible',14),(169,'08:00:00.000000','08:20:00.000000','disponible',15),(170,'08:20:00.000000','08:40:00.000000','reservado',15),(171,'08:40:00.000000','09:00:00.000000','disponible',15),(172,'09:00:00.000000','09:20:00.000000','disponible',15),(173,'09:20:00.000000','09:40:00.000000','disponible',15),(174,'09:40:00.000000','10:00:00.000000','disponible',15),(175,'10:00:00.000000','10:20:00.000000','disponible',15),(176,'10:20:00.000000','10:40:00.000000','disponible',15),(177,'10:40:00.000000','11:00:00.000000','disponible',15),(178,'11:00:00.000000','11:20:00.000000','disponible',15),(179,'11:20:00.000000','11:40:00.000000','disponible',15),(180,'11:40:00.000000','12:00:00.000000','disponible',15);
/*!40000 ALTER TABLE `agendaapp_bloquehorario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agendaapp_especialidad`
--

DROP TABLE IF EXISTS `agendaapp_especialidad`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agendaapp_especialidad` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) NOT NULL,
  `tipo` varchar(20) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agendaapp_especialidad`
--

LOCK TABLES `agendaapp_especialidad` WRITE;
/*!40000 ALTER TABLE `agendaapp_especialidad` DISABLE KEYS */;
INSERT INTO `agendaapp_especialidad` VALUES (1,'Medicina General','medicina_general'),(2,'Control Cronico - Diabetes','programa'),(3,'Matroneria','programa');
/*!40000 ALTER TABLE `agendaapp_especialidad` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agendaapp_hora`
--

DROP TABLE IF EXISTS `agendaapp_hora`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agendaapp_hora` (
  `id` char(32) NOT NULL,
  `estado` varchar(12) NOT NULL,
  `motivo_cancelacion` longtext NOT NULL,
  `creado_en` datetime(6) NOT NULL,
  `bloque_id` bigint(20) NOT NULL,
  `bloque_activo_id` bigint(20) DEFAULT NULL,
  `paciente_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `bloque_activo_id` (`bloque_activo_id`),
  KEY `agendaApp_hora_bloque_id_21b4b6e6_fk_agendaApp_bloquehorario_id` (`bloque_id`),
  KEY `agendaApp_hora_paciente_id_57bf0a81_fk_autentica` (`paciente_id`),
  CONSTRAINT `agendaApp_hora_bloque_activo_id_6859f79c_fk_agendaApp` FOREIGN KEY (`bloque_activo_id`) REFERENCES `agendaapp_bloquehorario` (`id`),
  CONSTRAINT `agendaApp_hora_bloque_id_21b4b6e6_fk_agendaApp_bloquehorario_id` FOREIGN KEY (`bloque_id`) REFERENCES `agendaapp_bloquehorario` (`id`),
  CONSTRAINT `agendaApp_hora_paciente_id_57bf0a81_fk_autentica` FOREIGN KEY (`paciente_id`) REFERENCES `autenticacionapp_paciente` (`usuario_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agendaapp_hora`
--

LOCK TABLES `agendaapp_hora` WRITE;
/*!40000 ALTER TABLE `agendaapp_hora` DISABLE KEYS */;
INSERT INTO `agendaapp_hora` VALUES ('26bd64f4efbb4533b2b155839ecce55b','confirmada','','2026-11-02 00:36:41.952039',158,158,'9e62d9b5c91a44c68d4a4f712d74bf38'),('281c001ca21f49f8b847024622049661','reservada','','2026-11-02 00:36:41.945528',143,143,'dd59ddbf72cf431db4fe0738860afbf7'),('2ef997fae7fd48e0b9f82319dea37f9a','confirmada','','2026-11-02 00:36:41.957041',60,60,'bf0fdc5a301b4670a2efe5dc9cf14b99'),('5a6309275f344780a254a59f215868a4','confirmada','','2026-11-02 00:36:41.951040',99,99,'b8280f3834a94c768c21a58edd029748'),('6752047055ca4b9c8434fb374d54b5a5','reservada','','2026-11-02 00:36:41.941530',13,13,'3dd6d41676bf4bcaa8d8e9a139608b0c'),('6dae3fa958e041619e74e100559ae6db','confirmada','','2026-11-02 00:36:41.954039',16,16,'2436f1fa5b8a41cdb8da55c3a9a6c784'),('714f90f6e0a042c29fac26b2319efece','reservada','','2026-11-02 00:36:41.943529',20,20,'c62917d2f1774a0381ba8727a23075cd'),('75da86bfc2264a81bd99ccee2b6fa02b','reservada','','2026-11-02 00:36:41.937528',39,39,'e90d00f12b5e41cf828408b2b37b3527'),('790bf85d542b4290a27d4b0a4178bc75','cancelada','','2026-11-02 00:36:41.960046',28,NULL,'31b7183a4a76474789b149e04fda11a0'),('81aaaa8b066e4662a5ab9aace9c5ddb4','cancelada','','2026-11-02 00:36:41.959046',10,NULL,'e90d00f12b5e41cf828408b2b37b3527'),('8e20edba3dde49fa8edaaf29da7058de','reservada','','2026-11-02 00:36:41.935713',83,83,'bf0fdc5a301b4670a2efe5dc9cf14b99'),('d77f11f0617d4f9b98572e314644254f','reservada','','2026-11-02 00:36:41.947033',27,27,'3ee8ea0f486b41c885d84fb2416ebfc5'),('e8c0ddbc272c4f6cac70151df5b2defb','reservada','','2026-11-02 00:36:41.938528',104,104,'31b7183a4a76474789b149e04fda11a0'),('f02557a050c644dd8ae8d1c6603e6da1','confirmada','','2026-11-02 00:36:41.955039',138,138,'822abb2fc8674e9a9dce79be2ff385f5'),('f108f4d6ea874acc978432c08b2776e2','reservada','','2026-11-02 00:36:41.939528',170,170,'79ce4a42656e4871b6e3099aa421c149');
/*!40000 ALTER TABLE `agendaapp_hora` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autenticacionapp_codigoenrolamiento`
--

DROP TABLE IF EXISTS `autenticacionapp_codigoenrolamiento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autenticacionapp_codigoenrolamiento` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `codigo_hash` varchar(64) NOT NULL,
  `creado_en` datetime(6) NOT NULL,
  `expira_en` datetime(6) NOT NULL,
  `usado_en` datetime(6) DEFAULT NULL,
  `intentos` smallint(5) unsigned NOT NULL CHECK (`intentos` >= 0),
  `creado_por_id` char(32) DEFAULT NULL,
  `usuario_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `autenticacionApp_cod_creado_por_id_53bffd70_fk_autentica` (`creado_por_id`),
  KEY `autenticacionApp_cod_usuario_id_e51c9032_fk_autentica` (`usuario_id`),
  CONSTRAINT `autenticacionApp_cod_creado_por_id_53bffd70_fk_autentica` FOREIGN KEY (`creado_por_id`) REFERENCES `autenticacionapp_usuario` (`id`),
  CONSTRAINT `autenticacionApp_cod_usuario_id_e51c9032_fk_autentica` FOREIGN KEY (`usuario_id`) REFERENCES `autenticacionapp_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autenticacionapp_codigoenrolamiento`
--

LOCK TABLES `autenticacionapp_codigoenrolamiento` WRITE;
/*!40000 ALTER TABLE `autenticacionapp_codigoenrolamiento` DISABLE KEYS */;
/*!40000 ALTER TABLE `autenticacionapp_codigoenrolamiento` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autenticacionapp_consentimiento`
--

DROP TABLE IF EXISTS `autenticacionapp_consentimiento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autenticacionapp_consentimiento` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `version` varchar(10) NOT NULL,
  `aceptado` tinyint(1) NOT NULL,
  `fecha` datetime(6) NOT NULL,
  `retirado_en` datetime(6) DEFAULT NULL,
  `usuario_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `autenticacionApp_con_usuario_id_2bf80c61_fk_autentica` (`usuario_id`),
  CONSTRAINT `autenticacionApp_con_usuario_id_2bf80c61_fk_autentica` FOREIGN KEY (`usuario_id`) REFERENCES `autenticacionapp_usuario` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autenticacionapp_consentimiento`
--

LOCK TABLES `autenticacionapp_consentimiento` WRITE;
/*!40000 ALTER TABLE `autenticacionapp_consentimiento` DISABLE KEYS */;
INSERT INTO `autenticacionapp_consentimiento` VALUES (1,'1.0',1,'2026-11-02 00:36:41.780479',NULL,'48cf683ba3534fba81f73834da5517ff'),(2,'1.0',1,'2026-11-02 00:36:41.781479',NULL,'cf218d08a24849cc91c7969fce027a4d'),(3,'1.0',1,'2026-11-02 00:36:41.782480',NULL,'bf0fdc5a301b4670a2efe5dc9cf14b99'),(4,'1.0',1,'2026-11-02 00:36:41.783478',NULL,'e90d00f12b5e41cf828408b2b37b3527'),(5,'1.0',1,'2026-11-02 00:36:41.784478',NULL,'31b7183a4a76474789b149e04fda11a0'),(6,'1.0',1,'2026-11-02 00:36:41.785478',NULL,'79ce4a42656e4871b6e3099aa421c149'),(7,'1.0',1,'2026-11-02 00:36:41.786478',NULL,'3dd6d41676bf4bcaa8d8e9a139608b0c'),(8,'1.0',1,'2026-11-02 00:36:41.787487',NULL,'c62917d2f1774a0381ba8727a23075cd'),(9,'1.0',1,'2026-11-02 00:36:41.788490',NULL,'dd59ddbf72cf431db4fe0738860afbf7'),(10,'1.0',1,'2026-11-02 00:36:41.789479',NULL,'3ee8ea0f486b41c885d84fb2416ebfc5'),(11,'1.0',1,'2026-11-02 00:36:41.789479',NULL,'b8280f3834a94c768c21a58edd029748'),(12,'1.0',1,'2026-11-02 00:36:41.790485',NULL,'9e62d9b5c91a44c68d4a4f712d74bf38'),(13,'1.0',1,'2026-11-02 00:36:41.791485',NULL,'2436f1fa5b8a41cdb8da55c3a9a6c784'),(14,'1.0',1,'2026-11-02 00:36:41.791485',NULL,'822abb2fc8674e9a9dce79be2ff385f5');
/*!40000 ALTER TABLE `autenticacionapp_consentimiento` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autenticacionapp_credencialpasskey`
--

DROP TABLE IF EXISTS `autenticacionapp_credencialpasskey`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autenticacionapp_credencialpasskey` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `credencial_id` varchar(255) NOT NULL,
  `clave_publica` longblob NOT NULL,
  `contador_firmas` bigint(20) unsigned NOT NULL CHECK (`contador_firmas` >= 0),
  `dispositivo` varchar(120) NOT NULL,
  `creada_en` datetime(6) NOT NULL,
  `ultimo_uso` datetime(6) DEFAULT NULL,
  `usuario_id` char(32) NOT NULL,
  `rp_id` varchar(253) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `credencial_id` (`credencial_id`),
  KEY `autenticacionApp_cre_usuario_id_8764cf49_fk_autentica` (`usuario_id`),
  CONSTRAINT `autenticacionApp_cre_usuario_id_8764cf49_fk_autentica` FOREIGN KEY (`usuario_id`) REFERENCES `autenticacionapp_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autenticacionapp_credencialpasskey`
--

LOCK TABLES `autenticacionapp_credencialpasskey` WRITE;
/*!40000 ALTER TABLE `autenticacionapp_credencialpasskey` DISABLE KEYS */;
/*!40000 ALTER TABLE `autenticacionapp_credencialpasskey` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autenticacionapp_paciente`
--

DROP TABLE IF EXISTS `autenticacionapp_paciente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autenticacionapp_paciente` (
  `usuario_id` char(32) NOT NULL,
  `ficha_clinica_id` varchar(20) NOT NULL,
  `sector_id` bigint(20) DEFAULT NULL,
  `tutor_id` char(32) DEFAULT NULL,
  `estado_inscripcion` varchar(10) NOT NULL,
  `prevision` varchar(15) NOT NULL,
  `prevision_consultada_en` datetime(6) DEFAULT NULL,
  `tramo` varchar(1) NOT NULL,
  PRIMARY KEY (`usuario_id`),
  KEY `autenticacionApp_pac_sector_id_eda019db_fk_autentica` (`sector_id`),
  KEY `autenticacionApp_pac_tutor_id_6e3c545d_fk_autentica` (`tutor_id`),
  CONSTRAINT `autenticacionApp_pac_sector_id_eda019db_fk_autentica` FOREIGN KEY (`sector_id`) REFERENCES `autenticacionapp_sector` (`id`),
  CONSTRAINT `autenticacionApp_pac_tutor_id_6e3c545d_fk_autentica` FOREIGN KEY (`tutor_id`) REFERENCES `autenticacionapp_usuario` (`id`),
  CONSTRAINT `autenticacionApp_pac_usuario_id_8b437c85_fk_autentica` FOREIGN KEY (`usuario_id`) REFERENCES `autenticacionapp_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autenticacionapp_paciente`
--

LOCK TABLES `autenticacionapp_paciente` WRITE;
/*!40000 ALTER TABLE `autenticacionapp_paciente` DISABLE KEYS */;
INSERT INTO `autenticacionapp_paciente` VALUES ('2436f1fa5b8a41cdb8da55c3a9a6c784','FC-1010',2,NULL,'vigente','fonasa',NULL,'C'),('31b7183a4a76474789b149e04fda11a0','FC-1002',3,NULL,'vigente','fonasa',NULL,'C'),('3dd6d41676bf4bcaa8d8e9a139608b0c','FC-1004',2,NULL,'vigente','fonasa',NULL,'A'),('3ee8ea0f486b41c885d84fb2416ebfc5','FC-1007',2,NULL,'vigente','fonasa',NULL,'D'),('79ce4a42656e4871b6e3099aa421c149','FC-1003',1,NULL,'vigente','fonasa',NULL,'D'),('822abb2fc8674e9a9dce79be2ff385f5','FC-1011',3,NULL,'vigente','fonasa',NULL,'D'),('9e62d9b5c91a44c68d4a4f712d74bf38','FC-1009',1,NULL,'vigente','fonasa',NULL,'B'),('b8280f3834a94c768c21a58edd029748','FC-1008',3,NULL,'vigente','fonasa',NULL,'A'),('bf0fdc5a301b4670a2efe5dc9cf14b99','FC-1000',1,'48cf683ba3534fba81f73834da5517ff','vigente','fonasa',NULL,'A'),('c62917d2f1774a0381ba8727a23075cd','FC-1005',3,NULL,'vigente','fonasa',NULL,'B'),('dd59ddbf72cf431db4fe0738860afbf7','FC-1006',1,NULL,'vigente','fonasa',NULL,'C'),('e90d00f12b5e41cf828408b2b37b3527','FC-1001',2,'cf218d08a24849cc91c7969fce027a4d','vigente','fonasa',NULL,'B');
/*!40000 ALTER TABLE `autenticacionapp_paciente` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autenticacionapp_profesional`
--

DROP TABLE IF EXISTS `autenticacionapp_profesional`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autenticacionapp_profesional` (
  `usuario_id` char(32) NOT NULL,
  `box_atencion` varchar(10) NOT NULL,
  `especialidad_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`usuario_id`),
  KEY `autenticacionApp_pro_especialidad_id_026cb4bc_fk_agendaApp` (`especialidad_id`),
  CONSTRAINT `autenticacionApp_pro_especialidad_id_026cb4bc_fk_agendaApp` FOREIGN KEY (`especialidad_id`) REFERENCES `agendaapp_especialidad` (`id`),
  CONSTRAINT `autenticacionApp_pro_usuario_id_a3765e4a_fk_autentica` FOREIGN KEY (`usuario_id`) REFERENCES `autenticacionapp_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autenticacionapp_profesional`
--

LOCK TABLES `autenticacionapp_profesional` WRITE;
/*!40000 ALTER TABLE `autenticacionapp_profesional` DISABLE KEYS */;
INSERT INTO `autenticacionapp_profesional` VALUES ('2d3b2d08c6324492af4e76185f16fe49','B-01',1),('94d9e05dd1944957bc3f62b88f161a34','B-03',3),('e9ccb03123cd4587b05b549a12811b35','B-02',2);
/*!40000 ALTER TABLE `autenticacionapp_profesional` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autenticacionapp_sector`
--

DROP TABLE IF EXISTS `autenticacionapp_sector`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autenticacionapp_sector` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(60) NOT NULL,
  `comuna` varchar(60) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autenticacionapp_sector`
--

LOCK TABLES `autenticacionapp_sector` WRITE;
/*!40000 ALTER TABLE `autenticacionapp_sector` DISABLE KEYS */;
INSERT INTO `autenticacionapp_sector` VALUES (1,'Sector 1','La Granja'),(2,'Sector 2','La Granja'),(3,'Sector 3','La Granja');
/*!40000 ALTER TABLE `autenticacionapp_sector` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autenticacionapp_solicitudderechos`
--

DROP TABLE IF EXISTS `autenticacionapp_solicitudderechos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autenticacionapp_solicitudderechos` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tipo` varchar(20) NOT NULL,
  `detalle` longtext NOT NULL,
  `estado` varchar(10) NOT NULL,
  `creada_en` datetime(6) NOT NULL,
  `respuesta` longtext NOT NULL,
  `resuelta_en` datetime(6) DEFAULT NULL,
  `resuelta_por_id` char(32) DEFAULT NULL,
  `usuario_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `autenticacionApp_sol_resuelta_por_id_c63a72cf_fk_autentica` (`resuelta_por_id`),
  KEY `autenticacionApp_sol_usuario_id_18aeec04_fk_autentica` (`usuario_id`),
  CONSTRAINT `autenticacionApp_sol_resuelta_por_id_c63a72cf_fk_autentica` FOREIGN KEY (`resuelta_por_id`) REFERENCES `autenticacionapp_usuario` (`id`),
  CONSTRAINT `autenticacionApp_sol_usuario_id_18aeec04_fk_autentica` FOREIGN KEY (`usuario_id`) REFERENCES `autenticacionapp_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autenticacionapp_solicitudderechos`
--

LOCK TABLES `autenticacionapp_solicitudderechos` WRITE;
/*!40000 ALTER TABLE `autenticacionapp_solicitudderechos` DISABLE KEYS */;
/*!40000 ALTER TABLE `autenticacionapp_solicitudderechos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autenticacionapp_usuario`
--

DROP TABLE IF EXISTS `autenticacionapp_usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autenticacionapp_usuario` (
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  `id` char(32) NOT NULL,
  `rut` varchar(12) DEFAULT NULL,
  `telefono` longtext NOT NULL,
  `tipo_usuario` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  UNIQUE KEY `rut` (`rut`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autenticacionapp_usuario`
--

LOCK TABLES `autenticacionapp_usuario` WRITE;
/*!40000 ALTER TABLE `autenticacionapp_usuario` DISABLE KEYS */;
INSERT INTO `autenticacionapp_usuario` VALUES ('!HQyEBNBztcm8hRKLDEXte5sSGxzkE7qm7WIp4xIh',NULL,0,'demo_30000004','Sofia','Ramirez Cortes','sofia.30000004@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.754959','1ce8c823b5d64e3094fd602f2e565297','30000004-5','','administrativo'),('!OuSXzzPrjYH8E90WkGWl10qiq1m6td8Wxue8rSNx',NULL,0,'demo_30000017','Ines','Sepulveda Toro','ines.30000017@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.775464','2436f1fa5b8a41cdb8da55c3a9a6c784','30000017-7','','paciente'),('!O1zyCp0TOOI4Ea3IjeYwWtek6zu71cSLoIsISWsh',NULL,0,'demo_30000001','Valentina','Rojas Soto','valentina.30000001@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.743912','2d3b2d08c6324492af4e76185f16fe49','30000001-0','','profesional'),('!0xjqBkk8FzN69j2HSIA0l7rkgHqOL6QPiF4FTt7z',NULL,0,'demo_30000009','Carmen','Silva Araya','carmen.30000009@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.762464','31b7183a4a76474789b149e04fda11a0','30000009-6','','paciente'),('!BvF6QpxZQbsiDMrBdeZ1mekcNVhC2wmpcDtbPWqi',NULL,0,'demo_30000011','Elena','Contreras Paz','elena.30000011@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.765464','3dd6d41676bf4bcaa8d8e9a139608b0c','30000011-8','','paciente'),('!hKWw0OW05zjoxRE2uMJP2jy4XWkjdRcmbo8tTNqM',NULL,0,'demo_30000014','Hector','Pizarro Olivares','hector.30000014@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.770465','3ee8ea0f486b41c885d84fb2416ebfc5','30000014-2','','paciente'),('!jD3WJCUf1Z0ilEoDJWhAYJZ08oqDACdwcBRn8jsy',NULL,0,'demo_30000005','Patricia','Morales Vega','patricia.30000005@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.755956','48cf683ba3534fba81f73834da5517ff','30000005-3','','tutor'),('!LIAlmEoJQrR1VV7ip0gxLnXfIkbYQOEYj6lKLPYz',NULL,0,'demo_30000010','Pedro','Munoz Tapia','pedro.30000010@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.763464','79ce4a42656e4871b6e3099aa421c149','30000010-K','','paciente'),('!Gn3Oiwx3a4AW4gLAYPSvP2UMdaq6HyKYTAqjjOAW',NULL,0,'demo_30000018','Oscar','Alarcon Mella','oscar.30000018@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.778478','822abb2fc8674e9a9dce79be2ff385f5','30000018-5','','paciente'),('!xrwSHTY5ds2ciKF5aH1CY8NV5Vj2DZdHsLD8JDTt',NULL,0,'demo_30000003','Camila','Navarro Pino','camila.30000003@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.751957','94d9e05dd1944957bc3f62b88f161a34','30000003-7','','profesional'),('!BGv4aQS2fdiqEksUmJJeUjrNtgKUCROnzDIKzkzK',NULL,0,'demo_30000016','Raul','Carrasco Bravo','raul.30000016@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.774464','9e62d9b5c91a44c68d4a4f712d74bf38','30000016-9','','paciente'),('!B0qNS57DgLqYxaCtdcrLgaywphCGWXZbWkXj5LBV',NULL,0,'demo_30000015','Gloria','Saavedra Nunez','gloria.30000015@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.772464','b8280f3834a94c768c21a58edd029748','30000015-0','','paciente'),('!V1YF7fWiWlhRIL3yf5tTmOR4r6hNcZwwidSKu9QK',NULL,0,'demo_30000007','Rosa','Gonzalez Mena','rosa.30000007@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.758464','bf0fdc5a301b4670a2efe5dc9cf14b99','30000007-K','','paciente'),('!9v85ITUQU6W2hgvviylQ1rM3VmQyHpKSsNhpV4mX',NULL,0,'demo_30000012','Manuel','Vargas Reyes','manuel.30000012@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.767465','c62917d2f1774a0381ba8727a23075cd','30000012-6','','paciente'),('!5W97972ablkjdAOmgDTZ8Gmd2R3sC20A6Biky8qH',NULL,0,'demo_30000006','Jorge','Castillo Ruiz','jorge.30000006@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.757460','cf218d08a24849cc91c7969fce027a4d','30000006-1','','tutor'),('!e6BItrvfPSme7MojMsLTM98PRBp9UQqsJRYw7yU0',NULL,0,'demo_30000013','Teresa','Espinoza Leiva','teresa.30000013@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.769464','dd59ddbf72cf431db4fe0738860afbf7','30000013-4','','paciente'),('!ZqOAF8uz8qTzz4bnLgVohrfQ5fVPlxWSMwwfeP4O',NULL,0,'demo_30000008','Luis','Herrera Diaz','luis.30000008@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.760464','e90d00f12b5e41cf828408b2b37b3527','30000008-8','','paciente'),('!hzV2w2Bx1AktZ42D2qwzCIHQx1CtYGrjUUQdXora',NULL,0,'demo_30000002','Matias','Fuentes Lagos','matias.30000002@correo-ficticio.cl',0,1,'2026-11-02 00:36:41.748957','e9ccb03123cd4587b05b549a12811b35','30000002-9','','profesional');
/*!40000 ALTER TABLE `autenticacionapp_usuario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autenticacionapp_usuario_groups`
--

DROP TABLE IF EXISTS `autenticacionapp_usuario_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autenticacionapp_usuario_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `usuario_id` char(32) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `autenticacionApp_usuario_usuario_id_group_id_7dbb1d9f_uniq` (`usuario_id`,`group_id`),
  KEY `autenticacionApp_usu_group_id_07dd8a4f_fk_auth_grou` (`group_id`),
  CONSTRAINT `autenticacionApp_usu_group_id_07dd8a4f_fk_auth_grou` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `autenticacionApp_usu_usuario_id_d1dcc996_fk_autentica` FOREIGN KEY (`usuario_id`) REFERENCES `autenticacionapp_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autenticacionapp_usuario_groups`
--

LOCK TABLES `autenticacionapp_usuario_groups` WRITE;
/*!40000 ALTER TABLE `autenticacionapp_usuario_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `autenticacionapp_usuario_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `autenticacionapp_usuario_user_permissions`
--

DROP TABLE IF EXISTS `autenticacionapp_usuario_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `autenticacionapp_usuario_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `usuario_id` char(32) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `autenticacionApp_usuario_usuario_id_permission_id_9412665b_uniq` (`usuario_id`,`permission_id`),
  KEY `autenticacionApp_usu_permission_id_09c3c480_fk_auth_perm` (`permission_id`),
  CONSTRAINT `autenticacionApp_usu_permission_id_09c3c480_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `autenticacionApp_usu_usuario_id_5b7aee55_fk_autentica` FOREIGN KEY (`usuario_id`) REFERENCES `autenticacionapp_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `autenticacionapp_usuario_user_permissions`
--

LOCK TABLES `autenticacionapp_usuario_user_permissions` WRITE;
/*!40000 ALTER TABLE `autenticacionapp_usuario_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `autenticacionapp_usuario_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=77 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add user',6,'add_usuario'),(22,'Can change user',6,'change_usuario'),(23,'Can delete user',6,'delete_usuario'),(24,'Can view user',6,'view_usuario'),(25,'Can add sector',7,'add_sector'),(26,'Can change sector',7,'change_sector'),(27,'Can delete sector',7,'delete_sector'),(28,'Can view sector',7,'view_sector'),(29,'Can add profesional',8,'add_profesional'),(30,'Can change profesional',8,'change_profesional'),(31,'Can delete profesional',8,'delete_profesional'),(32,'Can view profesional',8,'view_profesional'),(33,'Can add paciente',9,'add_paciente'),(34,'Can change paciente',9,'change_paciente'),(35,'Can delete paciente',9,'delete_paciente'),(36,'Can view paciente',9,'view_paciente'),(37,'Can add passkey',10,'add_credencialpasskey'),(38,'Can change passkey',10,'change_credencialpasskey'),(39,'Can delete passkey',10,'delete_credencialpasskey'),(40,'Can view passkey',10,'view_credencialpasskey'),(41,'Can add código de enrolamiento',11,'add_codigoenrolamiento'),(42,'Can change código de enrolamiento',11,'change_codigoenrolamiento'),(43,'Can delete código de enrolamiento',11,'delete_codigoenrolamiento'),(44,'Can view código de enrolamiento',11,'view_codigoenrolamiento'),(45,'Can add solicitud de derechos',12,'add_solicitudderechos'),(46,'Can change solicitud de derechos',12,'change_solicitudderechos'),(47,'Can delete solicitud de derechos',12,'delete_solicitudderechos'),(48,'Can view solicitud de derechos',12,'view_solicitudderechos'),(49,'Can add consentimiento',13,'add_consentimiento'),(50,'Can change consentimiento',13,'change_consentimiento'),(51,'Can delete consentimiento',13,'delete_consentimiento'),(52,'Can view consentimiento',13,'view_consentimiento'),(53,'Can add agenda',14,'add_agenda'),(54,'Can change agenda',14,'change_agenda'),(55,'Can delete agenda',14,'delete_agenda'),(56,'Can view agenda',14,'view_agenda'),(57,'Can add bloque horario',15,'add_bloquehorario'),(58,'Can change bloque horario',15,'change_bloquehorario'),(59,'Can delete bloque horario',15,'delete_bloquehorario'),(60,'Can view bloque horario',15,'view_bloquehorario'),(61,'Can add especialidad',16,'add_especialidad'),(62,'Can change especialidad',16,'change_especialidad'),(63,'Can delete especialidad',16,'delete_especialidad'),(64,'Can view especialidad',16,'view_especialidad'),(65,'Can add hora',17,'add_hora'),(66,'Can change hora',17,'change_hora'),(67,'Can delete hora',17,'delete_hora'),(68,'Can view hora',17,'view_hora'),(69,'Can add paciente en espera',18,'add_esperapaciente'),(70,'Can change paciente en espera',18,'change_esperapaciente'),(71,'Can delete paciente en espera',18,'delete_esperapaciente'),(72,'Can view paciente en espera',18,'view_esperapaciente'),(73,'Can add notificacion',19,'add_registronotificacion'),(74,'Can change notificacion',19,'change_registronotificacion'),(75,'Can delete notificacion',19,'delete_registronotificacion'),(76,'Can view notificacion',19,'view_registronotificacion');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_autenticacionApp_usuario_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_autenticacionApp_usuario_id` FOREIGN KEY (`user_id`) REFERENCES `autenticacionapp_usuario` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(14,'agendaApp','agenda'),(15,'agendaApp','bloquehorario'),(16,'agendaApp','especialidad'),(17,'agendaApp','hora'),(11,'autenticacionApp','codigoenrolamiento'),(13,'autenticacionApp','consentimiento'),(10,'autenticacionApp','credencialpasskey'),(9,'autenticacionApp','paciente'),(8,'autenticacionApp','profesional'),(7,'autenticacionApp','sector'),(12,'autenticacionApp','solicitudderechos'),(6,'autenticacionApp','usuario'),(3,'auth','group'),(2,'auth','permission'),(4,'contenttypes','contenttype'),(18,'listaEsperaApp','esperapaciente'),(19,'notificacionesApp','registronotificacion'),(5,'sessions','session');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-11-02 00:36:38.925135'),(2,'contenttypes','0002_remove_content_type_name','2026-11-02 00:36:38.954182'),(3,'auth','0001_initial','2026-11-02 00:36:39.085305'),(4,'auth','0002_alter_permission_name_max_length','2026-11-02 00:36:39.114570'),(5,'auth','0003_alter_user_email_max_length','2026-11-02 00:36:39.118082'),(6,'auth','0004_alter_user_username_opts','2026-11-02 00:36:39.121082'),(7,'auth','0005_alter_user_last_login_null','2026-11-02 00:36:39.123088'),(8,'auth','0006_require_contenttypes_0002','2026-11-02 00:36:39.124080'),(9,'auth','0007_alter_validators_add_error_messages','2026-11-02 00:36:39.127092'),(10,'auth','0008_alter_user_username_max_length','2026-11-02 00:36:39.130089'),(11,'auth','0009_alter_user_last_name_max_length','2026-11-02 00:36:39.133088'),(12,'auth','0010_alter_group_name_max_length','2026-11-02 00:36:39.139083'),(13,'auth','0011_update_proxy_permissions','2026-11-02 00:36:39.143084'),(14,'auth','0012_alter_user_first_name_max_length','2026-11-02 00:36:39.146082'),(15,'agendaApp','0001_initial','2026-11-02 00:36:39.233995'),(16,'autenticacionApp','0001_initial','2026-11-02 00:36:39.530283'),(17,'admin','0001_initial','2026-11-02 00:36:39.609776'),(18,'admin','0002_logentry_remove_auto_add','2026-11-02 00:36:39.620312'),(19,'admin','0003_logentry_add_action_flag_choices','2026-11-02 00:36:39.626146'),(20,'agendaApp','0002_initial','2026-11-02 00:36:39.819176'),(21,'agendaApp','0003_consentimiento_y_cifrado','2026-11-02 00:36:39.860562'),(22,'agendaApp','0004_cifrar_motivos_existentes','2026-11-02 00:36:39.892179'),(23,'autenticacionApp','0002_passkeys_enrolamiento','2026-11-02 00:36:40.027404'),(24,'autenticacionApp','0003_passkey_dominio','2026-11-02 00:36:40.038426'),(25,'autenticacionApp','0004_consentimiento_y_cifrado','2026-11-02 00:36:40.202581'),(26,'autenticacionApp','0005_cifrar_telefonos_existentes','2026-11-02 00:36:40.213089'),(27,'autenticacionApp','0006_prevision_paciente','2026-11-02 00:36:40.278318'),(28,'listaEsperaApp','0001_initial','2026-11-02 00:36:40.373190'),(29,'notificacionesApp','0001_initial','2026-11-02 00:36:40.418545'),(30,'sessions','0001_initial','2026-11-02 00:36:40.439515');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `listaesperaapp_esperapaciente`
--

DROP TABLE IF EXISTS `listaesperaapp_esperapaciente`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `listaesperaapp_esperapaciente` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `orden` int(10) unsigned NOT NULL CHECK (`orden` >= 0),
  `creado_en` datetime(6) NOT NULL,
  `especialidad_id` bigint(20) NOT NULL,
  `paciente_id` char(32) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `listaEsperaApp_esper_paciente_id_a31abf04_fk_autentica` (`paciente_id`),
  KEY `listaEspera_especia_3bb2a0_idx` (`especialidad_id`,`orden`),
  CONSTRAINT `listaEsperaApp_esper_especialidad_id_0a9032f8_fk_agendaApp` FOREIGN KEY (`especialidad_id`) REFERENCES `agendaapp_especialidad` (`id`),
  CONSTRAINT `listaEsperaApp_esper_paciente_id_a31abf04_fk_autentica` FOREIGN KEY (`paciente_id`) REFERENCES `autenticacionapp_paciente` (`usuario_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `listaesperaapp_esperapaciente`
--

LOCK TABLES `listaesperaapp_esperapaciente` WRITE;
/*!40000 ALTER TABLE `listaesperaapp_esperapaciente` DISABLE KEYS */;
INSERT INTO `listaesperaapp_esperapaciente` VALUES (1,1,'2026-11-02 00:36:41.963046',1,'9e62d9b5c91a44c68d4a4f712d74bf38'),(2,2,'2026-11-02 00:36:41.964062',1,'2436f1fa5b8a41cdb8da55c3a9a6c784'),(3,3,'2026-11-02 00:36:41.965067',1,'822abb2fc8674e9a9dce79be2ff385f5');
/*!40000 ALTER TABLE `listaesperaapp_esperapaciente` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notificacionesapp_registronotificacion`
--

DROP TABLE IF EXISTS `notificacionesapp_registronotificacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `notificacionesapp_registronotificacion` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `canal` varchar(10) NOT NULL,
  `estado` varchar(10) NOT NULL,
  `enviado_en` datetime(6) DEFAULT NULL,
  `hora_id` char(32) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `notificacionesApp_re_hora_id_17467d9f_fk_agendaApp` (`hora_id`),
  CONSTRAINT `notificacionesApp_re_hora_id_17467d9f_fk_agendaApp` FOREIGN KEY (`hora_id`) REFERENCES `agendaapp_hora` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notificacionesapp_registronotificacion`
--

LOCK TABLES `notificacionesapp_registronotificacion` WRITE;
/*!40000 ALTER TABLE `notificacionesapp_registronotificacion` DISABLE KEYS */;
/*!40000 ALTER TABLE `notificacionesapp_registronotificacion` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed
