"""
SOFTWARE ID
Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación - UNAD
Fase 4

from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
import logging
import re


# ============================================================
# 1. CONFIGURACIÓN DEL REGISTRO DE EVENTOS Y ERRORES
# ============================================================

CARPETA_PROYECTO = Path(__file__).resolve().parent
CARPETA_LOGS = CARPETA_PROYECTO / "logs"
CARPETA_LOGS.mkdir(parents=True, exist_ok=True)
ARCHIVO_LOG = CARPETA_LOGS / "software_id.log"

logger = logging.getLogger("SoftwareID")
logger.setLevel(logging.INFO)

if not logger.handlers:
    manejador = logging.FileHandler(ARCHIVO_LOG, encoding="utf-8")
    formato = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    manejador.setFormatter(formato)
    logger.addHandler(manejador)


# ============================================================
# 2. EXCEPCIONES PERSONALIZADAS
# ============================================================

class SoftwareIDError(Exception):
    """Excepción base de la aplicación."""


class ClienteInvalidoError(SoftwareIDError):
    """Se presenta cuando los datos de un cliente no son válidos."""


class ServicioNoDisponibleError(SoftwareIDError):
    """Se presenta cuando un servicio no existe o no está disponible."""


class ReservaInvalidaError(SoftwareIDError):
    """Se presenta cuando los datos de una reserva son incorrectos."""


class OperacionNoPermitidaError(SoftwareIDError):
    """Se presenta cuando una operación no corresponde al estado actual."""


class DatosFaltantesError(SoftwareIDError):
    """Se presenta cuando faltan datos obligatorios."""


# ============================================================
# 3. CLASE ABSTRACTA ENTIDAD
# ============================================================

class Entidad(ABC):
    """Clase abstracta que representa una entidad general del sistema."""

    def __init__(self, identificador):
        if not isinstance(identificador, str) or not identificador.strip():
            raise DatosFaltantesError(
                "El identificador de la entidad es obligatorio."
            )
        self._identificador = identificador.strip()

    @property
    def identificador(self):
        """Devuelve el identificador sin permitir su modificación directa."""
        return self._identificador

    @abstractmethod
    def obtener_informacion(self):
        """Cada entidad derivada debe implementar este método."""
        raise NotImplementedError


# ============================================================
# 4. CLASE CLIENTE
# ============================================================

class Cliente(Entidad):
    """Representa un cliente y encapsula sus datos personales."""

    def __init__(self, identificador, nombre, correo, telefono):
        super().__init__(identificador)

        if not all(
            isinstance(valor, str) and valor.strip()
            for valor in (nombre, correo, telefono)
        ):
            raise DatosFaltantesError(
                "El nombre, correo y teléfono son obligatorios."
            )

        patron_correo = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.fullmatch(patron_correo, correo.strip()):
            raise ClienteInvalidoError(
                "El formato del correo electrónico no es válido."
            )

        if not re.fullmatch(r"[0-9+\-\s]{7,18}", telefono.strip()):
            raise ClienteInvalidoError(
                "El teléfono debe contener entre 7 y 18 caracteres numéricos."
            )

        self.__nombre = nombre.strip()
        self.__correo = correo.strip().lower()
        self.__telefono = telefono.strip()

    @property
    def nombre(self):
        return self.__nombre

    @property
    def correo(self):
        return self.__correo

    @property
    def telefono(self):
        return self.__telefono

    def obtener_informacion(self):
        return (
            f"ID: {self.identificador} | Nombre: {self.nombre} | "
            f"Correo: {self.correo} | Teléfono: {self.telefono}"
        )

    def __str__(self):
        return self.obtener_informacion()


# ============================================================
# 5. CLASE ABSTRACTA SERVICIO
# ============================================================

class Servicio(Entidad, ABC):
    """Clase abstracta para los diferentes servicios de Software ID."""

    def __init__(self, identificador, nombre, precio_base):
        super().__init__(identificador)

        if not isinstance(nombre, str) or not nombre.strip():
            raise DatosFaltantesError("El nombre del servicio es obligatorio.")

        if (
            isinstance(precio_base, bool)
            or not isinstance(precio_base, (int, float))
            or precio_base <= 0
        ):
            raise ServicioNoDisponibleError(
                "El precio base debe ser un número positivo."
            )

        self._nombre = nombre.strip()
        self._precio_base = float(precio_base)
        self._disponible = True

    @property
    def nombre(self):
        return self._nombre

    @property
    def precio_base(self):
        return self._precio_base

    @property
    def disponible(self):
        return self._disponible

    def cambiar_disponibilidad(self, estado):
        if not isinstance(estado, bool):
            raise ValueError("La disponibilidad debe ser True o False.")
        self._disponible = estado
        logger.info(
            "Disponibilidad del servicio %s cambiada a %s",
            self.identificador, estado
        )

    def calcular_costo(self, duracion=1, impuesto=0, descuento=0):
        """
        Calcula el costo usando parámetros opcionales.
        Permite calcular costo básico, con impuesto, con descuento
        o con ambos. Es una adaptación de la sobrecarga a Python.
        """
        if not self.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self.nombre}' no está disponible."
            )

        if (
            isinstance(duracion, bool)
            or not isinstance(duracion, (int, float))
            or duracion <= 0
        ):
            raise ValueError("La duración debe ser un número positivo.")

        if not 0 <= impuesto <= 100:
            raise ValueError("El impuesto debe estar entre 0 y 100.")

        if not 0 <= descuento <= 100:
            raise ValueError("El descuento debe estar entre 0 y 100.")

        subtotal = self.precio_base * duracion
        valor_descuento = subtotal * descuento / 100
        base_gravable = subtotal - valor_descuento
        valor_impuesto = base_gravable * impuesto / 100

        return round(base_gravable + valor_impuesto, 2)

    @abstractmethod
    def describir(self):
        """Devuelve la descripción específica del servicio."""
        raise NotImplementedError

    @abstractmethod
    def validar_parametros(self, **kwargs):
        """Valida los parámetros particulares de cada servicio."""
        raise NotImplementedError

    def obtener_informacion(self):
        return self.describir()


# ============================================================
# 6. SERVICIO ESPECIALIZADO: RESERVA DE SALAS
# ============================================================

class ReservaSala(Servicio):
    """Servicio para reservar salas por horas."""

    def __init__(self, identificador, nombre, precio_base, capacidad):
        super().__init__(identificador, nombre, precio_base)
        self.validar_parametros(capacidad=capacidad)
        self._capacidad = capacidad

    def validar_parametros(self, **kwargs):
        capacidad = kwargs.get("capacidad")
        if (
            isinstance(capacidad, bool)
            or not isinstance(capacidad, int)
            or capacidad <= 0
        ):
            raise DatosFaltantesError(
                "La capacidad debe ser un número entero positivo."
            )

    def calcular_costo(self, duracion=1, impuesto=0, descuento=0):
        return super().calcular_costo(duracion, impuesto, descuento)

    def describir(self):
        return (
            f"Reserva de sala: {self.nombre} | "
            f"Tarifa por hora: ${self.precio_base:,.2f} | "
            f"Capacidad: {self._capacidad} personas"
        )


# ============================================================
# 7. SERVICIO ESPECIALIZADO: ALQUILER DE EQUIPOS
# ============================================================

class AlquilerEquipo(Servicio):
    """Servicio para alquilar equipos por días."""

    def __init__(self, identificador, nombre, precio_base, equipo):
        super().__init__(identificador, nombre, precio_base)
        self.validar_parametros(equipo=equipo)
        self._equipo = equipo.strip()

    def validar_parametros(self, **kwargs):
        equipo = kwargs.get("equipo")
        if not isinstance(equipo, str) or not equipo.strip():
            raise DatosFaltantesError(
                "Debe especificar el equipo que se desea alquilar."
            )

    def calcular_costo(self, duracion=1, impuesto=0, descuento=0):
        return super().calcular_costo(duracion, impuesto, descuento)

    def describir(self):
        return (
            f"Alquiler de equipo: {self.nombre} | "
            f"Equipo: {self._equipo} | "
            f"Tarifa por día: ${self.precio_base:,.2f}"
        )


# ============================================================
# 8. SERVICIO ESPECIALIZADO: ASESORÍAS
# ============================================================

class AsesoriaEspecializada(Servicio):
    """Servicio de asesorías especializadas por horas."""

    def __init__(self, identificador, nombre, precio_base, especialidad):
        super().__init__(identificador, nombre, precio_base)
        self.validar_parametros(especialidad=especialidad)
        self._especialidad = especialidad.strip()

    def validar_parametros(self, **kwargs):
        especialidad = kwargs.get("especialidad")
        if not isinstance(especialidad, str) or not especialidad.strip():
            raise DatosFaltantesError(
                "Debe especificar la especialidad de la asesoría."
            )

    def calcular_costo(self, duracion=1, impuesto=0, descuento=0):
        return super().calcular_costo(duracion, impuesto, descuento)

    def describir(self):
        return (
            f"Asesoría especializada: {self.nombre} | "
            f"Especialidad: {self._especialidad} | "
            f"Tarifa por hora: ${self.precio_base:,.2f}"
        )


# ============================================================
# 9. CLASE RESERVA
# ============================================================

class Reserva(Entidad):
    """Relaciona un cliente con un servicio y controla su estado."""

    def __init__(
        self, identificador, cliente, servicio, duracion,
        impuesto=0, descuento=0
    ):
        super().__init__(identificador)

        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("Debe asociar un cliente válido.")

        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("Debe asociar un servicio válido.")

        if (
            isinstance(duracion, bool)
            or not isinstance(duracion, (int, float))
            or duracion <= 0
        ):
            raise ReservaInvalidaError(
                "La duración de la reserva debe ser positiva."
            )

        self._cliente = cliente
        self._servicio = servicio
        self._duracion = float(duracion)
        self._estado = "PENDIENTE"

        try:
            self._costo_total = servicio.calcular_costo(
                self._duracion,
                impuesto=impuesto,
                descuento=descuento
            )
        except Exception as error:
            logger.exception(
                "No se pudo calcular el costo de la reserva %s",
                identificador
            )
            # Encadenamiento de excepciones: conserva la causa original.
            raise ReservaInvalidaError(
                "No fue posible calcular el costo de la reserva."
            ) from error

        logger.info("Reserva %s creada.", identificador)

    @property
    def cliente(self):
        return self._cliente

    @property
    def servicio(self):
        return self._servicio

    @property
    def duracion(self):
        return self._duracion

    @property
    def estado(self):
        return self._estado

    @property
    def costo_total(self):
        return self._costo_total

    def confirmar(self):
        if self._estado != "PENDIENTE":
            raise OperacionNoPermitidaError(
                f"No se puede confirmar una reserva en estado {self._estado}."
            )

        self._estado = "CONFIRMADA"
        logger.info("Reserva %s confirmada.", self.identificador)

    def cancelar(self):
        if self._estado not in ("PENDIENTE", "CONFIRMADA"):
            raise OperacionNoPermitidaError(
                f"No se puede cancelar una reserva en estado {self._estado}."
            )

        self._estado = "CANCELADA"
        logger.info("Reserva %s cancelada.", self.identificador)

    def procesar(self):
        if self._estado != "CONFIRMADA":
            raise OperacionNoPermitidaError(
                "Solo se pueden procesar reservas confirmadas."
            )

        self._estado = "PROCESADA"
        logger.info("Reserva %s procesada.", self.identificador)

    def obtener_informacion(self):
        return (
            f"Reserva: {self.identificador} | "
            f"Cliente: {self.cliente.nombre} | "
            f"Servicio: {self.servicio.nombre} | "
            f"Duración: {self.duracion:g} | "
            f"Estado: {self.estado} | "
            f"Total: ${self.costo_total:,.2f}"
        )


# ============================================================
# 10. GESTOR GENERAL DEL SISTEMA
# ============================================================

class GestorSistema:
    """Administra las listas de clientes, servicios y reservas."""

    def __init__(self):
        self._clientes = []
        self._servicios = []
        self._reservas = []

    @property
    def clientes(self):
        return tuple(self._clientes)

    @property
    def servicios(self):
        return tuple(self._servicios)

    @property
    def reservas(self):
        return tuple(self._reservas)

    def registrar_cliente(self, cliente):
        try:
            if not isinstance(cliente, Cliente):
                raise ClienteInvalidoError("El objeto no corresponde a un cliente.")

            if any(
                actual.identificador == cliente.identificador
                for actual in self._clientes
            ):
                raise ClienteInvalidoError(
                    "Ya existe un cliente con ese identificador."
                )

            if any(
                actual.correo == cliente.correo
                for actual in self._clientes
            ):
                raise ClienteInvalidoError(
                    "Ya existe un cliente con ese correo electrónico."
                )

            self._clientes.append(cliente)

        except Exception:
            logger.exception("Error al registrar un cliente.")
            raise

        else:
            logger.info("Cliente %s registrado correctamente.", cliente.identificador)
            return cliente

        finally:
            logger.info("Finalizó el intento de registro de cliente.")

    def registrar_servicio(self, servicio):
        if not isinstance(servicio, Servicio):
            raise ServicioNoDisponibleError(
                "El objeto proporcionado no es un servicio válido."
            )

        if any(
            actual.identificador == servicio.identificador
            for actual in self._servicios
        ):
            logger.error(
                "Intento de registrar servicio duplicado: %s",
                servicio.identificador
            )
            raise ServicioNoDisponibleError(
                "Ya existe un servicio con ese identificador."
            )

        self._servicios.append(servicio)
        logger.info("Servicio %s registrado.", servicio.identificador)
        return servicio

    def crear_reserva(
        self, id_reserva, id_cliente, id_servicio, duracion,
        impuesto=0, descuento=0
    ):
        cliente = next(
            (c for c in self._clientes if c.identificador == id_cliente),
            None
        )
        servicio = next(
            (s for s in self._servicios if s.identificador == id_servicio),
            None
        )

        if cliente is None:
            raise ReservaInvalidaError(
                f"No se encontró el cliente {id_cliente}."
            )

        if servicio is None:
            raise ServicioNoDisponibleError(
                f"No se encontró el servicio {id_servicio}."
            )

        if any(
            actual.identificador == id_reserva
            for actual in self._reservas
        ):
            raise ReservaInvalidaError(
                "Ya existe una reserva con ese identificador."
            )

        reserva = Reserva(
            id_reserva, cliente, servicio, duracion,
            impuesto=impuesto, descuento=descuento
        )
        self._reservas.append(reserva)
        logger.info("Reserva %s agregada al sistema.", id_reserva)
        return reserva

    def generar_resumen(self):
        lineas = [
            "========== RESUMEN DEL SISTEMA ==========",
            f"Clientes registrados: {len(self._clientes)}",
            f"Servicios registrados: {len(self._servicios)}",
            f"Reservas registradas: {len(self._reservas)}",
            "",
            "--------------- CLIENTES ---------------"
        ]

        if self._clientes:
            lineas.extend(c.obtener_informacion() for c in self._clientes)
        else:
            lineas.append("No hay clientes registrados.")

        lineas.append("")
        lineas.append("--------------- SERVICIOS ---------------")
        if self._servicios:
            lineas.extend(s.describir() for s in self._servicios)
        else:
            lineas.append("No hay servicios registrados.")

        lineas.append("")
        lineas.append("--------------- RESERVAS ---------------")
        if self._reservas:
            lineas.extend(r.obtener_informacion() for r in self._reservas)
        else:
            lineas.append("No hay reservas registradas.")

        return "\n".join(lineas)


# ============================================================
# 11. DEMOSTRACIÓN DE OPERACIONES
# ============================================================

def ejecutar_demostracion():
    """
    Ejecuta más de diez operaciones completas, tanto exitosas
    como fallidas, para demostrar la robustez del sistema.
    """
    gestor = GestorSistema()

    print("\n" + "=" * 58)
    print("       DEMOSTRACIÓN DEL SISTEMA SOFTWARE ID")
    print("=" * 58)

    # Operación 1: registrar un cliente válido.
    cliente1 = Cliente(
        "C001", "Laura Gómez", "laura@gmail.com", "3001234567"
    )
    gestor.registrar_cliente(cliente1)
    print("1. Cliente Laura Gómez registrado correctamente.")

    # Operación 2: registrar un segundo cliente.
    cliente2 = Cliente(
        "C002", "Andrés Ruiz", "andres@correo.com", "3107654321"
    )
    gestor.registrar_cliente(cliente2)
    print("2. Cliente Andrés Ruiz registrado correctamente.")

    # Operación 3: intentar registrar un correo incorrecto.
    try:
        Cliente("C003", "Cliente Inválido", "correo-no-valido", "3001112233")
    except ClienteInvalidoError as error:
        logger.warning("Operación 3: %s", error)
        print(f"3. Error controlado al registrar cliente: {error}")

    # Operación 4: registrar un servicio de sala.
    sala = ReservaSala(
        "S001", "Sala de conferencias", 50000, capacidad=12
    )
    gestor.registrar_servicio(sala)
    print("4. Servicio de reserva de sala registrado.")

    # Operación 5: registrar un servicio de alquiler de equipo.
    equipo = AlquilerEquipo(
        "S002", "Alquiler de video beam", 35000, equipo="Video beam"
    )
    gestor.registrar_servicio(equipo)
    print("5. Servicio de alquiler de equipo registrado.")

    # Operación 6: registrar una asesoría especializada.
    asesoria = AsesoriaEspecializada(
        "S003", "Asesoría en software", 80000,
        especialidad="Desarrollo de software"
    )
    gestor.registrar_servicio(asesoria)
    print("6. Servicio de asesoría especializada registrado.")

    # Operación 7: intentar crear un servicio con precio negativo.
    try:
        ReservaSala("S004", "Sala inválida", -1000, capacidad=10)
    except ServicioNoDisponibleError as error:
        logger.warning("Operación 7: %s", error)
        print(f"7. Error controlado al crear servicio: {error}")

    # Operación 8: crear una reserva válida.
    reserva1 = gestor.crear_reserva("R001", "C001", "S001", 2)
    print(
        f"8. Reserva R001 creada. Costo: ${reserva1.costo_total:,.2f}"
    )

    # Operación 9: confirmar la reserva.
    reserva1.confirmar()
    print("9. Reserva R001 confirmada.")

    # Operación 10: crear y cancelar una segunda reserva.
    reserva2 = gestor.crear_reserva("R002", "C002", "S002", 3)
    reserva2.cancelar()
    print("10. Reserva R002 creada y cancelada.")

    # Operación 11: intentar procesar una reserva cancelada.
    try:
        reserva2.procesar()
    except OperacionNoPermitidaError as error:
        logger.warning("Operación 11: %s", error)
        print(f"11. Error controlado al procesar reserva: {error}")

    # Operación 12: intentar reservar un servicio inexistente.
    try:
        gestor.crear_reserva("R003", "C001", "S999", 1)
    except ServicioNoDisponibleError as error:
        logger.warning("Operación 12: %s", error)
        print(f"12. Error controlado al crear reserva: {error}")

    # Operación 13: procesar correctamente la primera reserva.
    reserva1.procesar()
    print("13. Reserva R001 procesada correctamente.")

    # Operación 14: calcular costo con impuesto y descuento.
    costo_especial = sala.calcular_costo(
        duracion=2, impuesto=19, descuento=10
    )
    print(
        "14. Cálculo con descuento del 10 % e impuesto del 19 %: "
        f"${costo_especial:,.2f}"
    )

    print("\n" + gestor.generar_resumen())
    print(f"\nLos eventos y errores se registraron en: {ARCHIVO_LOG}")
    print("=" * 58)


# ============================================================
# 12. MENÚ INTERACTIVO DE CONSOLA
# ============================================================

def menu_interactivo():
    """Permite utilizar las funciones del sistema desde la terminal."""
    gestor = GestorSistema()

    while True:
        print("\n" + "=" * 48)
        print("          SISTEMA SOFTWARE ID")
        print("=" * 48)
        print("1. Registrar cliente")
        print("2. Registrar servicio de sala")
        print("3. Registrar alquiler de equipo")
        print("4. Registrar asesoría especializada")
        print("5. Crear reserva")
        print("6. Confirmar reserva")
        print("7. Cancelar reserva")
        print("8. Procesar reserva")
        print("9. Consultar resumen del sistema")
        print("10. Ejecutar demostración automática")
        print("0. Salir")
        print("=" * 48)

        opcion = input("Seleccione una opción: ").strip()

        try:
            if opcion == "1":
                cliente = Cliente(
                    input("Identificador: ").strip(),
                    input("Nombre completo: ").strip(),
                    input("Correo electrónico: ").strip(),
                    input("Teléfono: ").strip()
                )
                gestor.registrar_cliente(cliente)
                print("Cliente registrado correctamente.")

            elif opcion == "2":
                servicio = ReservaSala(
                    input("Identificador del servicio: ").strip(),
                    input("Nombre de la sala: ").strip(),
                    float(input("Tarifa por hora: ")),
                    int(input("Capacidad de la sala: "))
                )
                gestor.registrar_servicio(servicio)
                print("Sala registrada correctamente.")

            elif opcion == "3":
                servicio = AlquilerEquipo(
                    input("Identificador del servicio: ").strip(),
                    input("Nombre del servicio: ").strip(),
                    float(input("Tarifa por día: ")),
                    input("Nombre del equipo: ").strip()
                )
                gestor.registrar_servicio(servicio)
                print("Equipo registrado correctamente.")

            elif opcion == "4":
                servicio = AsesoriaEspecializada(
                    input("Identificador del servicio: ").strip(),
                    input("Nombre del servicio: ").strip(),
                    float(input("Tarifa por hora: ")),
                    input("Especialidad: ").strip()
                )
                gestor.registrar_servicio(servicio)
                print("Asesoría registrada correctamente.")

            elif opcion == "5":
                reserva = gestor.crear_reserva(
                    input("Identificador de reserva: ").strip(),
                    input("Identificador del cliente: ").strip(),
                    input("Identificador del servicio: ").strip(),
                    float(input("Duración (horas o días): "))
                )
                print(
                    f"Reserva creada. Costo estimado: "
                    f"${reserva.costo_total:,.2f}"
                )

            elif opcion in ("6", "7", "8"):
                identificador = input(
                    "Identificador de la reserva: "
                ).strip()

                reserva = next(
                    (
                        r for r in gestor.reservas
                        if r.identificador == identificador
                    ),
                    None
                )

                if reserva is None:
                    raise ReservaInvalidaError(
                        "No se encontró la reserva indicada."
                    )

                if opcion == "6":
                    reserva.confirmar()
                    print("Reserva confirmada.")
                elif opcion == "7":
                    reserva.cancelar()
                    print("Reserva cancelada.")
                else:
                    reserva.procesar()
                    print("Reserva procesada.")

            elif opcion == "9":
                print(gestor.generar_resumen())

            elif opcion == "10":
                ejecutar_demostracion()

            elif opcion == "0":
                print("Gracias por utilizar Software ID.")
                logger.info("Aplicación cerrada por el usuario.")
                break

            else:
                print("Opción no válida. Intente nuevamente.")

        except (SoftwareIDError, ValueError) as error:
            logger.warning("Operación no completada: %s", error)
            print(f"\nNo fue posible completar la operación: {error}")

        except Exception as error:
            logger.exception("Error inesperado en el menú principal.")
            print(f"\nSe presentó un error inesperado: {error}")


# ============================================================
# 13. PUNTO DE ENTRADA
# ============================================================

if __name__ == "__main__":
    print("\nBIENVENIDO AL SISTEMA INTEGRAL SOFTWARE ID")
    print("1. Ingresar al menú interactivo")
    print("2. Ejecutar demostración automática")

    try:
        modo = input("Seleccione el modo de ejecución: ").strip()

        if modo == "2":
            ejecutar_demostracion()
        else:
            menu_interactivo()

    except KeyboardInterrupt:
        print("\nEjecución interrumpida por el usuario.")
        logger.warning("La ejecución fue interrumpida mediante teclado.")

    except Exception as error:
        logger.exception("Error crítico al iniciar la aplicación.")
        print(f"Error al iniciar Software ID: {error}")
