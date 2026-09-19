from django.db import transaction
from django.utils import timezone

from facturas.models import Factura, FacturaDetalle
from kardex.models import KardexDetalle, KardexMovimiento

from .models import Remision, RemisionReserva


class RemisionDomainError(Exception):
    pass


@transaction.atomic
def confirmar_remision(remision_id, observaciones=''):
    remision = Remision.objects.select_for_update().get(pk=remision_id)
    if remision.estado != Remision.Estado.PENDIENTE:
        raise RemisionDomainError('Solo se pueden confirmar remisiones pendientes.')
    if not remision.detalles.exists():
        raise RemisionDomainError('La remisión debe tener al menos un detalle.')
    remision.estado = Remision.Estado.CONFIRMADA
    remision.save(update_fields=['estado', 'actualizado_en'])
    return remision


@transaction.atomic
def reservar_remision(remision_id, observaciones=''):
    remision = Remision.objects.select_for_update().get(pk=remision_id)
    if remision.estado != Remision.Estado.CONFIRMADA:
        raise RemisionDomainError('Solo se pueden reservar remisiones confirmadas.')
    reserva = remision.reservas.select_for_update().filter(
        estado__in=[RemisionReserva.Estado.PENDIENTE, RemisionReserva.Estado.CONFIRMADA]
    ).first()
    if reserva:
        raise RemisionDomainError('La remisión ya tiene una reserva activa.')
    reserva = RemisionReserva.objects.create(
        remision=remision,
        estado=RemisionReserva.Estado.CONFIRMADA,
        confirmada_at=timezone.now(),
        observaciones=observaciones,
    )
    remision.estado = Remision.Estado.RESERVADA
    remision.save(update_fields=['estado', 'actualizado_en'])
    return remision, reserva


@transaction.atomic
def cancelar_remision(remision_id):
    remision = Remision.objects.select_for_update().get(pk=remision_id)
    if remision.estado in (Remision.Estado.ENTREGADA, Remision.Estado.CANCELADA):
        raise RemisionDomainError('La remisión no se puede cancelar en su estado actual.')
    remision.estado = Remision.Estado.CANCELADA
    remision.save(update_fields=['estado', 'actualizado_en'])
    remision.reservas.filter(
        estado__in=[RemisionReserva.Estado.PENDIENTE, RemisionReserva.Estado.CONFIRMADA]
    ).update(estado=RemisionReserva.Estado.CANCELADA, cancelada_at=timezone.now())
    return remision


@transaction.atomic
def entregar_remision(remision_id):
    remision = Remision.objects.select_for_update().get(pk=remision_id)
    if remision.estado not in (Remision.Estado.CONFIRMADA, Remision.Estado.RESERVADA):
        raise RemisionDomainError('La remisión debe estar confirmada o reservada para entregarse.')
    detalles = list(remision.detalles.select_related('producto'))
    if not detalles:
        raise RemisionDomainError('La remisión debe tener al menos un detalle.')

    movimiento = KardexMovimiento.objects.create(
        cliente=remision.cliente,
        tipo=KardexMovimiento.Tipo.VENTA,
        numero_documento=remision.numero,
        descripcion=f'Remisión {remision.numero}',
        valor=remision.total,
        remision=remision,
    )
    KardexDetalle.objects.bulk_create([
        KardexDetalle(
            movimiento=movimiento,
            producto=detalle.producto,
            cantidad=detalle.cantidad,
            precio_unitario=detalle.precio_unitario,
        )
        for detalle in detalles
    ])
    remision.estado = Remision.Estado.ENTREGADA
    remision.fecha_entrega_real = timezone.localdate()
    remision.save(update_fields=['estado', 'fecha_entrega_real', 'actualizado_en'])
    remision.reservas.filter(estado=RemisionReserva.Estado.CONFIRMADA).update(
        estado=RemisionReserva.Estado.CANCELADA,
        cancelada_at=timezone.now(),
    )
    return remision


@transaction.atomic
def facturar_remision(remision_id):
    remision = Remision.objects.select_for_update().get(pk=remision_id)
    factura = Factura.objects.filter(remision=remision).first()
    if factura:
        return remision, factura
    if remision.estado not in (Remision.Estado.CONFIRMADA, Remision.Estado.RESERVADA, Remision.Estado.ENTREGADA):
        raise RemisionDomainError('Solo se pueden facturar remisiones confirmadas, reservadas o entregadas.')
    factura = Factura.objects.create(
        numero=f'FAC-{timezone.now():%Y%m%d%H%M%S%f}',
        cliente=remision.cliente,
        remision=remision,
        fecha_emision=timezone.localdate(),
        estado=Factura.Estado.EMITIDA,
        subtotal=remision.subtotal,
        impuestos=remision.impuestos,
        total=remision.total,
    )
    factura.detalles.bulk_create([
        FacturaDetalle(
            factura=factura,
            producto=detalle.producto,
            descripcion=detalle.descripcion,
            cantidad=detalle.cantidad,
            precio_unitario=detalle.precio_unitario,
            subtotal=detalle.subtotal,
        )
        for detalle in remision.detalles.all()
    ])
    return remision, factura
