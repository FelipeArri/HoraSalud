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
INSERT INTO `agendaapp_agenda` VALUES (1,'2026-11-02',1,'899cf0c7abc642b0a3d63371f500e285'),(2,'2026-11-02',2,'621a9bbc08fb4025a5b86f90daede79d'),(3,'2026-11-02',3,'6e192908797548d896507ef019871c6c'),(4,'2026-11-03',1,'899cf0c7abc642b0a3d63371f500e285'),(5,'2026-11-03',2,'621a9bbc08fb4025a5b86f90daede79d'),(6,'2026-11-03',3,'6e192908797548d896507ef019871c6c'),(7,'2026-11-04',1,'899cf0c7abc642b0a3d63371f500e285'),(8,'2026-11-04',2,'621a9bbc08fb4025a5b86f90daede79d'),(9,'2026-11-04',3,'6e192908797548d896507ef019871c6c'),(10,'2026-11-05',1,'899cf0c7abc642b0a3d63371f500e285'),(11,'2026-11-05',2,'621a9bbc08fb4025a5b86f90daede79d'),(12,'2026-11-05',3,'6e192908797548d896507ef019871c6c'),(13,'2026-11-06',1,'899cf0c7abc642b0a3d63371f500e285'),(14,'2026-11-06',2,'621a9bbc08fb4025a5b86f90daede79d'),(15,'2026-11-06',3,'6e192908797548d896507ef019871c6c');
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
  `motivo_cancelacion` varchar(200) NOT NULL,
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
INSERT INTO `agendaapp_hora` VALUES ('063c4c25231b42c28cc5d5ce4024df4a','reservada','','2026-10-30 19:26:30.430314',83,83,'e090e5efd2be416ebc0da44407959ceb'),('0bfeb31afced47f2b0fb24c796987293','reservada','','2026-10-30 19:26:30.435794',143,143,'22d6f31a4017407f93ea8cbc15d18b5d'),('0cdbec465df24d1a96b7d6345a11f20a','confirmada','','2026-10-30 19:26:30.437869',138,138,'a5a28a867f674f3d93133818334c5d7f'),('17521a510025448a90c661c0135f6e86','confirmada','','2026-10-30 19:26:30.437869',60,60,'e090e5efd2be416ebc0da44407959ceb'),('1af088a02d104a1da4dc7c42abeec4d5','reservada','','2026-10-30 19:26:30.434796',13,13,'7ad1b8bb03d045fab19ee172a5fb19cd'),('337638b8b1fb4090af6493d505873927','cancelada','Paciente avisa que no puede asistir','2026-10-30 19:26:30.438870',10,NULL,'ea4513b6fca04c28b844e6ea31e989b6'),('3493605869c24267930619bae1fb6017','confirmada','','2026-10-30 19:26:30.436864',158,158,'046ec3bf40ff4d4fb77bdcfd76253014'),('952b9e626944485dadeaa6192f7b2b9b','reservada','','2026-10-30 19:26:30.431408',39,39,'ea4513b6fca04c28b844e6ea31e989b6'),('9aabe051af51453faf970847054782ba','reservada','','2026-10-30 19:26:30.435794',27,27,'e5244a10952f404b9bdfc5e86ac94a73'),('9b32e872c1cb4d0fa84ac022cd3a8fda','confirmada','','2026-10-30 19:26:30.436864',16,16,'c0936ceb29384199b8cf1b2e5f0e1c9d'),('ab4c680176364520afb39c1bd378aaed','reservada','','2026-10-30 19:26:30.433792',170,170,'5051fe161c754552b6d4c84376c5c5f1'),('ac2e15cd820e4bbe8f5d5150b2517aa5','reservada','','2026-10-30 19:26:30.433792',104,104,'d793245ba4304defb72c7e9b9907df62'),('adbd3fcd944e4f8f999bf15689e905d5','cancelada','Paciente avisa que no puede asistir','2026-10-30 19:26:30.438870',28,NULL,'d793245ba4304defb72c7e9b9907df62'),('cb51dde157224b6588acb002fef8c729','reservada','','2026-10-30 19:26:30.434796',20,20,'789dab0a12034e9a9ef8aca8aad06cdd'),('f0866ca6c1704683a73fab474aeb655a','confirmada','','2026-10-30 19:26:30.436864',99,99,'3d10ff596c44441fbef0d82b81e71254');
/*!40000 ALTER TABLE `agendaapp_hora` ENABLE KEYS */;
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
INSERT INTO `autenticacionapp_paciente` VALUES ('046ec3bf40ff4d4fb77bdcfd76253014','FC-1009',1,NULL),('22d6f31a4017407f93ea8cbc15d18b5d','FC-1006',1,NULL),('3d10ff596c44441fbef0d82b81e71254','FC-1008',3,NULL),('5051fe161c754552b6d4c84376c5c5f1','FC-1003',1,NULL),('789dab0a12034e9a9ef8aca8aad06cdd','FC-1005',3,NULL),('7ad1b8bb03d045fab19ee172a5fb19cd','FC-1004',2,NULL),('a5a28a867f674f3d93133818334c5d7f','FC-1011',3,NULL),('c0936ceb29384199b8cf1b2e5f0e1c9d','FC-1010',2,NULL),('d793245ba4304defb72c7e9b9907df62','FC-1002',3,NULL),('e090e5efd2be416ebc0da44407959ceb','FC-1000',1,'a6214f02f00e4eb1817075a0a7c18d88'),('e5244a10952f404b9bdfc5e86ac94a73','FC-1007',2,NULL),('ea4513b6fca04c28b844e6ea31e989b6','FC-1001',2,'c0b33eff40404cc99873361aff803282');
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
INSERT INTO `autenticacionapp_profesional` VALUES ('621a9bbc08fb4025a5b86f90daede79d','B-02',2),('6e192908797548d896507ef019871c6c','B-03',3),('899cf0c7abc642b0a3d63371f500e285','B-01',1);
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
  `telefono` varchar(20) NOT NULL,
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
INSERT INTO `autenticacionapp_usuario` VALUES ('!EihJ0Ct6uIHYvRZIfYzWFiRg28mrPVG7ayzxxwXS',NULL,0,'demo_30000016','Raul','Carrasco Bravo','raul.30000016@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.281257','046ec3bf40ff4d4fb77bdcfd76253014','30000016-9','+56900000016','paciente'),('!GjRFu2BccfFk5VFXPrlRGI34IcreFLOCS6g67lqr',NULL,0,'demo_30000013','Teresa','Espinoza Leiva','teresa.30000013@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.276256','22d6f31a4017407f93ea8cbc15d18b5d','30000013-4','+56900000013','paciente'),('!ybB1QczC2e6JJQvJqcJNSIaT6KDSzXu1ZxXb640X',NULL,0,'demo_30000015','Gloria','Saavedra Nunez','gloria.30000015@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.279259','3d10ff596c44441fbef0d82b81e71254','30000015-0','+56900000015','paciente'),('!iytEc9lQa2E2CdB2ssnIXOxiqg6GPbINVnzkAMLA',NULL,0,'demo_30000010','Pedro','Munoz Tapia','pedro.30000010@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.269394','5051fe161c754552b6d4c84376c5c5f1','30000010-K','+56900000010','paciente'),('!FPa9xtT86X9hvmt6M2xyk3qjDwCsQ4x35ZLs2QrZ',NULL,0,'demo_30000002','Matias','Fuentes Lagos','matias.30000002@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.254387','621a9bbc08fb4025a5b86f90daede79d','30000002-9','+56900000002','profesional'),('!mU0rNUI6J8XylTWCxrtJelBRkLaSShsjcIXFfMNL',NULL,0,'demo_30000003','Camila','Navarro Pino','camila.30000003@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.257393','6e192908797548d896507ef019871c6c','30000003-7','+56900000003','profesional'),('!X5KNl5O9ni5KQrFgEePQulY1OmNUqGyJRE6IEODM',NULL,0,'demo_30000012','Manuel','Vargas Reyes','manuel.30000012@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.274256','789dab0a12034e9a9ef8aca8aad06cdd','30000012-6','+56900000012','paciente'),('!xfydHha985iLI78KLmVMmqGNxNBZVTsxaONbyirE',NULL,0,'demo_30000011','Elena','Contreras Paz','elena.30000011@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.272257','7ad1b8bb03d045fab19ee172a5fb19cd','30000011-8','+56900000011','paciente'),('!VMWXciOPqzuajoTOLarbREVVz27aQKl3WKCpfnt3',NULL,0,'demo_30000004','Sofia','Ramirez Cortes','sofia.30000004@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.259394','880eddb7d1884079ac35c97b88a62ed3','30000004-5','+56900000004','administrativo'),('!k4MqN5Zh5WnzY1JNn51npYsx1PeevDKsKVTZsOR9',NULL,0,'demo_30000001','Valentina','Rojas Soto','valentina.30000001@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.250752','899cf0c7abc642b0a3d63371f500e285','30000001-0','+56900000001','profesional'),('!ej7ORPQ4lSUZhIrcUaOF4THGsLyZdUYiMK0KFkQx',NULL,0,'demo_30000018','Oscar','Alarcon Mella','oscar.30000018@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.285255','a5a28a867f674f3d93133818334c5d7f','30000018-5','+56900000018','paciente'),('!STg8Bpd2MxKDK4PAXU0jNVaxdneNBNRnLY5uussB',NULL,0,'demo_30000005','Patricia','Morales Vega','patricia.30000005@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.260410','a6214f02f00e4eb1817075a0a7c18d88','30000005-3','+56900000005','tutor'),('!MECAjcphWFiaUImCxlQ1I8HQcvWMNIBzBHTULw2n',NULL,0,'demo_30000017','Ines','Sepulveda Toro','ines.30000017@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.283258','c0936ceb29384199b8cf1b2e5f0e1c9d','30000017-7','+56900000017','paciente'),('!VarXq51saPGeDEEVFKUOUSdOna6D64NRcbeLuUfS',NULL,0,'demo_30000006','Jorge','Castillo Ruiz','jorge.30000006@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.261400','c0b33eff40404cc99873361aff803282','30000006-1','+56900000006','tutor'),('!GsurKs4zpdBYTvpSd0swnzolohJEXn4up3pO2unT',NULL,0,'demo_30000009','Carmen','Silva Araya','carmen.30000009@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.268394','d793245ba4304defb72c7e9b9907df62','30000009-6','+56900000009','paciente'),('!lK0lUk6udmFC9kPM6vKCSe1NbjVWyE5XFdAlMHzn',NULL,0,'demo_30000007','Rosa','Gonzalez Mena','rosa.30000007@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.263399','e090e5efd2be416ebc0da44407959ceb','30000007-K','+56900000007','paciente'),('!TSPYCaO5GIWPqzRgYXbkUqMOOq9Fw8ibwx61EPHA',NULL,0,'demo_30000014','Hector','Pizarro Olivares','hector.30000014@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.277261','e5244a10952f404b9bdfc5e86ac94a73','30000014-2','+56900000014','paciente'),('!juC1iU8psRgm6n2n1Kr5ky7HAAR5W2ViBFH6FcqI',NULL,0,'demo_30000008','Luis','Herrera Diaz','luis.30000008@correo-ficticio.cl',0,1,'2026-10-30 19:26:30.266401','ea4513b6fca04c28b844e6ea31e989b6','30000008-8','+56900000008','paciente');
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
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add content type',4,'add_contenttype'),(14,'Can change content type',4,'change_contenttype'),(15,'Can delete content type',4,'delete_contenttype'),(16,'Can view content type',4,'view_contenttype'),(17,'Can add session',5,'add_session'),(18,'Can change session',5,'change_session'),(19,'Can delete session',5,'delete_session'),(20,'Can view session',5,'view_session'),(21,'Can add user',6,'add_usuario'),(22,'Can change user',6,'change_usuario'),(23,'Can delete user',6,'delete_usuario'),(24,'Can view user',6,'view_usuario'),(25,'Can add sector',7,'add_sector'),(26,'Can change sector',7,'change_sector'),(27,'Can delete sector',7,'delete_sector'),(28,'Can view sector',7,'view_sector'),(29,'Can add profesional',8,'add_profesional'),(30,'Can change profesional',8,'change_profesional'),(31,'Can delete profesional',8,'delete_profesional'),(32,'Can view profesional',8,'view_profesional'),(33,'Can add paciente',9,'add_paciente'),(34,'Can change paciente',9,'change_paciente'),(35,'Can delete paciente',9,'delete_paciente'),(36,'Can view paciente',9,'view_paciente'),(37,'Can add agenda',10,'add_agenda'),(38,'Can change agenda',10,'change_agenda'),(39,'Can delete agenda',10,'delete_agenda'),(40,'Can view agenda',10,'view_agenda'),(41,'Can add bloque horario',11,'add_bloquehorario'),(42,'Can change bloque horario',11,'change_bloquehorario'),(43,'Can delete bloque horario',11,'delete_bloquehorario'),(44,'Can view bloque horario',11,'view_bloquehorario'),(45,'Can add especialidad',12,'add_especialidad'),(46,'Can change especialidad',12,'change_especialidad'),(47,'Can delete especialidad',12,'delete_especialidad'),(48,'Can view especialidad',12,'view_especialidad'),(49,'Can add hora',13,'add_hora'),(50,'Can change hora',13,'change_hora'),(51,'Can delete hora',13,'delete_hora'),(52,'Can view hora',13,'view_hora'),(53,'Can add paciente en espera',14,'add_esperapaciente'),(54,'Can change paciente en espera',14,'change_esperapaciente'),(55,'Can delete paciente en espera',14,'delete_esperapaciente'),(56,'Can view paciente en espera',14,'view_esperapaciente'),(57,'Can add notificacion',15,'add_registronotificacion'),(58,'Can change notificacion',15,'change_registronotificacion'),(59,'Can delete notificacion',15,'delete_registronotificacion'),(60,'Can view notificacion',15,'view_registronotificacion');
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
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (1,'admin','logentry'),(10,'agendaApp','agenda'),(11,'agendaApp','bloquehorario'),(12,'agendaApp','especialidad'),(13,'agendaApp','hora'),(9,'autenticacionApp','paciente'),(8,'autenticacionApp','profesional'),(7,'autenticacionApp','sector'),(6,'autenticacionApp','usuario'),(3,'auth','group'),(2,'auth','permission'),(4,'contenttypes','contenttype'),(14,'listaEsperaApp','esperapaciente'),(15,'notificacionesApp','registronotificacion'),(5,'sessions','session');
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
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2026-10-30 19:26:27.142823'),(2,'contenttypes','0002_remove_content_type_name','2026-10-30 19:26:27.210111'),(3,'auth','0001_initial','2026-10-30 19:26:27.483270'),(4,'auth','0002_alter_permission_name_max_length','2026-10-30 19:26:27.601682'),(5,'auth','0003_alter_user_email_max_length','2026-10-30 19:26:27.609751'),(6,'auth','0004_alter_user_username_opts','2026-10-30 19:26:27.617993'),(7,'auth','0005_alter_user_last_login_null','2026-10-30 19:26:27.624962'),(8,'auth','0006_require_contenttypes_0002','2026-10-30 19:26:27.628352'),(9,'auth','0007_alter_validators_add_error_messages','2026-10-30 19:26:27.635390'),(10,'auth','0008_alter_user_username_max_length','2026-10-30 19:26:27.643434'),(11,'auth','0009_alter_user_last_name_max_length','2026-10-30 19:26:27.648353'),(12,'auth','0010_alter_group_name_max_length','2026-10-30 19:26:27.662355'),(13,'auth','0011_update_proxy_permissions','2026-10-30 19:26:27.667203'),(14,'auth','0012_alter_user_first_name_max_length','2026-10-30 19:26:27.671210'),(15,'agendaApp','0001_initial','2026-10-30 19:26:27.824851'),(16,'autenticacionApp','0001_initial','2026-10-30 19:26:28.437553'),(17,'admin','0001_initial','2026-10-30 19:26:28.584061'),(18,'admin','0002_logentry_remove_auto_add','2026-10-30 19:26:28.605153'),(19,'admin','0003_logentry_add_action_flag_choices','2026-10-30 19:26:28.613156'),(20,'agendaApp','0002_initial','2026-10-30 19:26:28.931291'),(21,'listaEsperaApp','0001_initial','2026-10-30 19:26:29.075250'),(22,'notificacionesApp','0001_initial','2026-10-30 19:26:29.160782'),(23,'sessions','0001_initial','2026-10-30 19:26:29.208725');
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
INSERT INTO `listaesperaapp_esperapaciente` VALUES (1,1,'2026-10-30 19:26:30.439871',1,'046ec3bf40ff4d4fb77bdcfd76253014'),(2,2,'2026-10-30 19:26:30.440871',1,'c0936ceb29384199b8cf1b2e5f0e1c9d'),(3,3,'2026-10-30 19:26:30.441869',1,'a5a28a867f674f3d93133818334c5d7f');
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
