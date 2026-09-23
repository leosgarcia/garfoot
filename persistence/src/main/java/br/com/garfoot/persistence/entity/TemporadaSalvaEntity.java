package br.com.garfoot.persistence.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.util.UUID;

@Entity
@Table(name = "temporada_salva")
public class TemporadaSalvaEntity {
    @Id
    private UUID id;

    @Column(nullable = false, length = 160)
    private String nome;

    @Column(nullable = false, columnDefinition = "text")
    private String estadoJson;

    protected TemporadaSalvaEntity() { }

    public TemporadaSalvaEntity(UUID id, String nome, String estadoJson) {
        this.id = id;
        this.nome = nome;
        this.estadoJson = estadoJson;
    }

    public UUID getId() { return id; }
    public String getNome() { return nome; }
    public String getEstadoJson() { return estadoJson; }
}
