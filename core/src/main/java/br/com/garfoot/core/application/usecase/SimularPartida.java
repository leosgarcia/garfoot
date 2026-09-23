package br.com.garfoot.core.application.usecase;

import br.com.garfoot.core.engine.ForcaEquipe;
import br.com.garfoot.core.engine.MotorSimulacaoPartida;
import br.com.garfoot.core.engine.ResultadoSimulacao;
import br.com.garfoot.core.model.partida.Partida;

import java.util.Objects;

public final class SimularPartida {
    private final MotorSimulacaoPartida motor;

    public SimularPartida(MotorSimulacaoPartida motor) {
        this.motor = Objects.requireNonNull(motor, "motor must not be null");
    }

    public ResultadoSimulacao executar(Partida partida, ForcaEquipe forcaMandante, ForcaEquipe forcaVisitante, long seed) {
        Objects.requireNonNull(partida, "partida must not be null");
        ResultadoSimulacao resultado = motor.simular(forcaMandante, forcaVisitante,
                partida.mandante().elenco(), partida.visitante().elenco(), seed);
        resultado.aplicarA(partida);
        return resultado;
    }
}
