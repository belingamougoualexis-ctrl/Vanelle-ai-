package com.proofrail.app.data

data class Control(
    val id: Long,
    val name: String,
    val requirement: String,
    val threshold: Int,
    val createdAt: Long,
    val latestStatus: String?,
    val latestEvidenceCount: Int?
)

data class Evidence(
    val id: Long,
    val controlId: Long,
    val controlName: String,
    val source: String,
    val statement: String,
    val observedAt: String,
    val createdAt: Long
)

data class Decision(
    val id: Long,
    val title: String,
    val details: String,
    val risk: String,
    val requiredApprovals: Int,
    val status: String,
    val createdAt: Long,
    val decidedAt: Long?,
    val decidedBy: String?
)

data class AuditEvent(
    val id: Long,
    val action: String,
    val objectType: String,
    val objectId: Long?,
    val payload: String,
    val prevHash: String,
    val hash: String,
    val createdAt: Long
)

data class DashboardState(
    val controls: Int,
    val evidence: Int,
    val checks: Int,
    val decisionsPending: Int,
    val auditEntries: Int,
    val auditValid: Boolean
)

data class ChainVerification(
    val valid: Boolean,
    val entries: Int,
    val brokenId: Long? = null
)
