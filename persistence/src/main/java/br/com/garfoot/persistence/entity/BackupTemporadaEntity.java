package br.com.garfoot.persistence.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "backup_temporada")
public class BackupTemporadaEntity {
    @Id private UUID id;
    @Column(nullable = false) private UUID temporadaId;
    @Column(nullable = false) private Instant criadoEm;
    @Column(nullable = false, columnDefinition = "text") private String estadoJson;
    protected BackupTemporadaEntity() { }
    public BackupTemporadaEntity(UUID id, UUID temporadaId, Instant criadoEm, String estadoJson) {
        this.id=id; this.temporadaId=temporadaId; this.criadoEm=criadoEm; this.estadoJson=estadoJson;
    }
    public UUID getId() { return id; }
    public UUID getTemporadaId() { return temporadaId; }
    public Instant getCriadoEm() { return criadoEm; }
    public String getEstadoJson() { return estadoJson; }
}
