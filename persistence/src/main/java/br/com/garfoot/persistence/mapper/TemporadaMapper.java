package br.com.garfoot.persistence.mapper;

import br.com.garfoot.core.model.campeonato.Campeonato;
import br.com.garfoot.core.model.campeonato.ClassificacaoItem;
import br.com.garfoot.core.model.campeonato.Rodada;
import br.com.garfoot.core.model.campeonato.TipoCompeticao;
import br.com.garfoot.core.model.clube.Clube;
import br.com.garfoot.core.model.clube.Tecnico;
import br.com.garfoot.core.model.jogador.AtributosJogador;
import br.com.garfoot.core.model.jogador.Jogador;
import br.com.garfoot.core.model.jogador.Posicao;
import br.com.garfoot.core.model.jogador.StatusJogador;
import br.com.garfoot.core.model.partida.EventoPartida;
import br.com.garfoot.core.model.partida.Partida;
import br.com.garfoot.core.model.partida.StatusPartida;
import br.com.garfoot.core.model.partida.TipoEvento;
import br.com.garfoot.core.model.tatica.Escalacao;
import br.com.garfoot.core.model.tatica.EstiloJogo;
import br.com.garfoot.core.model.tatica.Formacao;
import br.com.garfoot.core.model.tatica.Tatica;
import br.com.garfoot.persistence.entity.TemporadaSalvaEntity;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Converts the framework-free season aggregate to a storage-only JSON snapshot. */
public final class TemporadaMapper {
    private final ObjectMapper json = new ObjectMapper();

    public TemporadaSalvaEntity toEntity(Campeonato campeonato) {
        try {
            EstadoTemporada estado = EstadoTemporada.from(campeonato);
            return new TemporadaSalvaEntity(campeonato.id(), campeonato.nome(), json.writeValueAsString(estado));
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("could not serialize season", exception);
        }
    }

    public Campeonato toDomain(TemporadaSalvaEntity entity) {
        try {
            EstadoTemporada estado = json.readValue(entity.getEstadoJson(), EstadoTemporada.class);
            return estado.toDomain();
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("could not deserialize season", exception);
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record EstadoTemporada(int versaoFormato, UUID id, String nome, String tipo, List<ClubeData> clubes,
                                  List<RodadaData> rodadas, List<ClassificacaoData> classificacao,
                                  String pais, String divisao, List<String> paisesDeCarreira,
                                  List<ClubeData> reservatorioDistrital) {
        private static final int VERSAO_ATUAL = 4;

        static EstadoTemporada from(Campeonato campeonato) {
            return new EstadoTemporada(VERSAO_ATUAL, campeonato.id(), campeonato.nome(), campeonato.tipo().name(),
                    campeonato.participantes().stream().map(ClubeData::from).toList(),
                    campeonato.rodadas().stream().map(RodadaData::from).toList(),
                    campeonato.classificacao().stream().map(ClassificacaoData::from).toList(), campeonato.pais(), campeonato.divisao(),
                    campeonato.paisesDeCarreira(), campeonato.reservatorioDistrital().stream().map(ClubeData::from).toList());
        }

        Campeonato toDomain() {
            if (versaoFormato < 1 || versaoFormato > VERSAO_ATUAL) {
                throw new IllegalStateException("unsupported season save format: " + versaoFormato);
            }
            Campeonato campeonato = new Campeonato(id, nome, TipoCompeticao.valueOf(tipo),
                    pais == null ? "Brasil" : pais, divisao == null ? "Série A" : divisao);
            if (paisesDeCarreira != null && !paisesDeCarreira.isEmpty()) campeonato.definirPaisesDeCarreira(paisesDeCarreira);
            Map<UUID, Clube> clubesPorId = new HashMap<>();
            Map<UUID, Jogador> jogadoresPorId = new HashMap<>();
            for (ClubeData clubeData : clubes) {
                Clube clube = clubeData.toDomain();
                clubeData.jogadores().forEach(j -> jogadoresPorId.put(j.id(), clube.elenco().stream()
                        .filter(item -> item.id().equals(j.id())).findFirst().orElseThrow()));
                if (clubeData.tecnicoId() != null && clubeData.tecnicoNome() != null)
                    clube.definirTecnico(new Tecnico(clubeData.tecnicoId(), clubeData.tecnicoNome()));
                if (clubeData.tatica() != null) clube.definirTatica(clubeData.tatica().toDomain(clube));
                clubesPorId.put(clube.id(), clube);
                campeonato.adicionarParticipante(clube);
            }
            for (RodadaData rodadaData : rodadas) {
                Rodada rodada = new Rodada(rodadaData.numero());
                for (PartidaData partidaData : rodadaData.partidas()) {
                    Clube mandante = clubesPorId.get(partidaData.mandanteId());
                    Clube visitante = clubesPorId.get(partidaData.visitanteId());
                    if (mandante == null || visitante == null) throw new IllegalStateException("match references unknown club");
                    Partida partida = new Partida(partidaData.id(), mandante, visitante,
                            LocalDateTime.parse(partidaData.dataHora()));
                    StatusPartida status = StatusPartida.valueOf(partidaData.status());
                    if (status != StatusPartida.AGENDADA) {
                        partida.iniciar();
                        for (int goal = 0; goal < partidaData.golsMandante(); goal++) partida.registrarGolMandante();
                        for (int goal = 0; goal < partidaData.golsVisitante(); goal++) partida.registrarGolVisitante();
                        for (EventoData evento : partidaData.eventos()) partida.registrarEvento(evento.toDomain(jogadoresPorId));
                        if (status == StatusPartida.ENCERRADA) partida.encerrar();
                    }
                    rodada.adicionarPartida(partida);
                }
                campeonato.adicionarRodada(rodada);
            }
            if (reservatorioDistrital != null) reservatorioDistrital.stream().map(ClubeData::toDomain).forEach(campeonato::adicionarAoDistrito);
            if (!classificacao.isEmpty()) {
                campeonato.atualizarClassificacao(classificacao.stream().map(item -> item.toDomain(clubesPorId)).toList());
            }
            return campeonato;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record ClubeData(UUID id, String nome, String sigla, List<JogadorData> jogadores,
                            UUID tecnicoId, String tecnicoNome, TaticaData tatica, long valorElencoEur, String pais,
                            boolean elencoSintetico, boolean elencoCompletadoSinteticamente) {
        static ClubeData from(Clube clube) {
            return new ClubeData(clube.id(), clube.nome(), clube.sigla(), clube.elenco().stream().map(JogadorData::from).toList(),
                    clube.tecnico() == null ? null : clube.tecnico().id(),
                    clube.tecnico() == null ? null : clube.tecnico().nome(),
                    clube.tatica() == null ? null : TaticaData.from(clube.tatica()), clube.valorElencoEur(), clube.pais(),
                    clube.elencoSintetico(), clube.elencoCompletadoSinteticamente());
        }
        Clube toDomain() {
            Clube clube = new Clube(id, nome, sigla);
            jogadores.stream().map(JogadorData::toDomain).forEach(clube::adicionarJogador);
            clube.definirValorElencoEur(Math.max(0, valorElencoEur));
            if (pais != null) clube.definirPais(pais);
            clube.definirElencoSintetico(elencoSintetico);
            clube.definirElencoCompletadoSinteticamente(elencoCompletadoSinteticamente);
            return clube;
        }
    }

    public record TaticaData(String nomeFormacao, List<String> posicoes, List<UUID> titulares,
                             List<UUID> reservas, String estilo) {
        static TaticaData from(Tatica tatica) {
            return new TaticaData(tatica.escalacao().formacao().nome(),
                    tatica.escalacao().formacao().posicoesTitulares().stream().map(Enum::name).toList(),
                    tatica.escalacao().titulares().stream().map(Jogador::id).toList(),
                    tatica.escalacao().reservas().stream().map(Jogador::id).toList(), tatica.estilo().name());
        }
        Tatica toDomain(Clube clube) {
            Map<UUID, Jogador> elenco = clube.elenco().stream().collect(java.util.stream.Collectors.toMap(Jogador::id, j -> j));
            List<Jogador> onze = titulares.stream().map(elenco::get).toList();
            List<Jogador> banco = reservas.stream().map(elenco::get).toList();
            Formacao formacao = new Formacao(nomeFormacao, posicoes.stream().map(Posicao::valueOf).toList());
            return new Tatica(new Escalacao(formacao, onze, banco), EstiloJogo.valueOf(estilo));
        }
    }

    public record JogadorData(UUID id, String nome, String nascimento, String posicao, int tecnica, int fisico,
                              int mental, int velocidade, int finalizacao, int passe, int marcacao, int potencial,
                              int moral, int condicao, String status) {
        static JogadorData from(Jogador j) {
            AtributosJogador a = j.atributos();
            return new JogadorData(j.id(), j.nome(), j.dataNascimento().toString(), j.posicao().name(), a.tecnica(),
                    a.fisico(), a.mental(), a.velocidade(), a.finalizacao(), a.passe(), a.marcacao(), a.potencial(),
                    j.moral(), j.condicaoFisica(), j.status().name());
        }
        Jogador toDomain() {
            Jogador j = new Jogador(id, nome, LocalDate.parse(nascimento), Posicao.valueOf(posicao),
                    new AtributosJogador(tecnica, fisico, mental, velocidade, finalizacao, passe, marcacao, potencial));
            j.atualizarMoral(moral);
            j.atualizarCondicaoFisica(condicao);
            j.atualizarStatus(StatusJogador.valueOf(status));
            return j;
        }
    }

    public record RodadaData(int numero, List<PartidaData> partidas) {
        static RodadaData from(Rodada rodada) {
            return new RodadaData(rodada.numero(), rodada.partidas().stream().map(PartidaData::from).toList());
        }
    }

    public record PartidaData(UUID id, UUID mandanteId, UUID visitanteId, String dataHora, String status,
                              int golsMandante, int golsVisitante, List<EventoData> eventos) {
        static PartidaData from(Partida partida) {
            return new PartidaData(partida.id(), partida.mandante().id(), partida.visitante().id(),
                    partida.dataHora().toString(), partida.status().name(), partida.golsMandante(), partida.golsVisitante(),
                    partida.eventos().stream().map(EventoData::from).toList());
        }
    }

    public record EventoData(int minuto, String tipo, UUID jogadorId, String descricao,
                             UUID jogadorQueSaiId, UUID jogadorQueEntraId) {
        static EventoData from(EventoPartida evento) {
            return new EventoData(evento.minuto(), evento.tipo().name(), id(evento.jogadorEnvolvido()),
                    evento.descricaoNarrativa(), id(evento.jogadorQueSai()), id(evento.jogadorQueEntra()));
        }
        EventoPartida toDomain(Map<UUID, Jogador> jogadores) {
            Jogador envolvido = jogadorId == null ? null : jogadores.get(jogadorId);
            Jogador sai = jogadorQueSaiId == null ? null : jogadores.get(jogadorQueSaiId);
            Jogador entra = jogadorQueEntraId == null ? null : jogadores.get(jogadorQueEntraId);
            return new EventoPartida(minuto, TipoEvento.valueOf(tipo), envolvido, descricao, sai, entra);
        }
        private static UUID id(Jogador jogador) { return jogador == null ? null : jogador.id(); }
    }

    public record ClassificacaoData(UUID clubeId, int pontos, int vitorias, int empates, int derrotas,
                                    int golsPro, int golsContra) {
        static ClassificacaoData from(ClassificacaoItem item) {
            return new ClassificacaoData(item.clube().id(), item.pontos(), item.vitorias(), item.empates(),
                    item.derrotas(), item.golsPro(), item.golsContra());
        }
        ClassificacaoItem toDomain(Map<UUID, Clube> clubes) {
            return new ClassificacaoItem(clubes.get(clubeId), pontos, vitorias, empates, derrotas, golsPro, golsContra);
        }
    }
}
