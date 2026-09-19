from rest_framework import serializers

from .models import Transportador, TransportadorVehiculo, Vehiculo, Viaje, ViajeRemision


class TransportadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transportador
        fields = '__all__'
        read_only_fields = ['codigo', 'creado_en', 'actualizado_en']


class VehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehiculo
        fields = '__all__'
        read_only_fields = ['creado_en']


class TransportadorVehiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransportadorVehiculo
        fields = '__all__'

    def validate(self, attrs):
        transportador = attrs.get(
            'transportador',
            getattr(self.instance, 'transportador', None),
        )
        vehiculo = attrs.get('vehiculo', getattr(self.instance, 'vehiculo', None))
        if transportador and transportador.estado != Transportador.Estado.ACTIVO:
            raise serializers.ValidationError({
                'transportador': 'El transportador no está activo.'
            })
        if vehiculo and vehiculo.estado != Vehiculo.Estado.ACTIVO:
            raise serializers.ValidationError({
                'vehiculo': 'El vehículo no está activo.'
            })
        return attrs


class ViajeSerializer(serializers.ModelSerializer):
    remisiones = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Viaje
        fields = '__all__'
        read_only_fields = ['codigo', 'creado_en', 'actualizado_en', 'remisiones']

    def validate(self, attrs):
        transportador = attrs.get('transportador', getattr(self.instance, 'transportador', None))
        vehiculo = attrs.get('vehiculo', getattr(self.instance, 'vehiculo', None))
        if transportador and transportador.estado != Transportador.Estado.ACTIVO:
            raise serializers.ValidationError({'transportador': 'El transportador no está activo.'})
        if vehiculo and vehiculo.estado != Vehiculo.Estado.ACTIVO:
            raise serializers.ValidationError({'vehiculo': 'El vehículo no está activo.'})
        if transportador and vehiculo and not TransportadorVehiculo.objects.filter(
            transportador=transportador,
            vehiculo=vehiculo,
            fecha_desasignacion__isnull=True,
        ).exists():
            raise serializers.ValidationError({
                'vehiculo': 'El vehículo no está asignado al transportador.'
            })
        return attrs


class ViajeRemisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ViajeRemision
        fields = '__all__'

    def validate(self, attrs):
        viaje = attrs.get('viaje', getattr(self.instance, 'viaje', None))
        remision = attrs.get('remision', getattr(self.instance, 'remision', None))
        if viaje and viaje.estado != Viaje.Estado.PROGRAMADO:
            raise serializers.ValidationError({
                'viaje': 'Solo se pueden asignar remisiones a viajes programados.'
            })
        if remision and remision.estado in (
            remision.Estado.ENTREGADA,
            remision.Estado.CANCELADA,
        ):
            raise serializers.ValidationError({
                'remision': 'La remisión no está disponible para asignación.'
            })
        if (
            viaje and remision and remision.transportador_id
            and remision.transportador_id != viaje.transportador_id
        ):
            raise serializers.ValidationError({
                'remision': 'La remisión pertenece a otro transportador.'
            })
        if remision and remision.asignaciones_viaje.exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError({
                'remision': 'La remisión ya está asignada a otro viaje.'
            })
        return attrs
