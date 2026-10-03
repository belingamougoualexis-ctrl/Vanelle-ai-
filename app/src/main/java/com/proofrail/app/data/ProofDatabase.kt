package com.proofrail.app.data

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest

class ProofDatabase(context: Context) : SQLiteOpenHelper(context, "proofrail.db", null, 1) {
    companion object {
        private const val DB_VERSION = 1
        private const val GENESIS = "GENESIS"
    }

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("PRAGMA foreign_keys=ON")
        db.execSQL("CREATE TABLE controls(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,requirement TEXT NOT NULL,threshold INTEGER NOT NULL,created_at INTEGER NOT NULL)")
        db.execSQL("CREATE TABLE evidence(id INTEGER PRIMARY KEY AUTOINCREMENT,control_id INTEGER NOT NULL REFERENCES controls(id) ON DELETE CASCADE,source TEXT NOT NULL,statement TEXT NOT NULL,observed_at TEXT NOT NULL,created_at INTEGER NOT NULL)")
        db.execSQL("CREATE TABLE checks(id INTEGER PRIMARY KEY AUTOINCREMENT,control_id INTEGER NOT NULL REFERENCES controls(id) ON DELETE CASCADE,status TEXT NOT NULL,evidence_count INTEGER NOT NULL,created_at INTEGER NOT NULL)")
        db.execSQL("CREATE TABLE decisions(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,details TEXT NOT NULL,risk TEXT NOT NULL,required_approvals INTEGER NOT NULL,status TEXT NOT NULL,created_at INTEGER NOT NULL,decided_at INTEGER,decided_by TEXT)")
        db.execSQL("CREATE TABLE audit(id INTEGER PRIMARY KEY AUTOINCREMENT,action TEXT NOT NULL,object_type TEXT NOT NULL,object_id INTEGER,payload TEXT NOT NULL,prev_hash TEXT NOT NULL,hash TEXT NOT NULL,created_at INTEGER NOT NULL)")
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit

    fun dashboard(): DashboardState = readableDatabase.use { db ->
        DashboardState(
            controls = count(db, "controls"),
            evidence = count(db, "evidence"),
            checks = count(db, "checks"),
            decisionsPending = db.rawQuery("SELECT COUNT(*) FROM decisions WHERE status='PENDING'", null).use { it.moveToFirst(); it.getInt(0) },
            auditEntries = count(db, "audit"),
            auditValid = verifyChain(db).valid
        )
    }

    fun listControls(): List<Control> = readableDatabase.use { db ->
        val result = mutableListOf<Control>()
        db.rawQuery(
            """SELECT c.*, x.status AS latest_status, x.evidence_count AS latest_evidence_count
               FROM controls c
               LEFT JOIN checks x ON x.id = (SELECT MAX(id) FROM checks WHERE control_id=c.id)
               ORDER BY c.id DESC""", null
        ).use { cur ->
            while (cur.moveToNext()) result += Control(
                cur.getLong(cur.getColumnIndexOrThrow("id")),
                cur.getString(cur.getColumnIndexOrThrow("name")),
                cur.getString(cur.getColumnIndexOrThrow("requirement")),
                cur.getInt(cur.getColumnIndexOrThrow("threshold")),
                cur.getLong(cur.getColumnIndexOrThrow("created_at")),
                cur.getString(cur.getColumnIndexOrThrow("latest_status")),
                if (cur.isNull(cur.getColumnIndexOrThrow("latest_evidence_count"))) null else cur.getInt(cur.getColumnIndexOrThrow("latest_evidence_count"))
            )
        }
        result
    }

    fun listEvidence(): List<Evidence> = readableDatabase.use { db ->
        val result = mutableListOf<Evidence>()
        db.rawQuery(
            """SELECT e.*, c.name AS control_name FROM evidence e JOIN controls c ON c.id=e.control_id ORDER BY e.id DESC""", null
        ).use { cur ->
            while (cur.moveToNext()) result += Evidence(
                cur.getLong(cur.getColumnIndexOrThrow("id")),
                cur.getLong(cur.getColumnIndexOrThrow("control_id")),
                cur.getString(cur.getColumnIndexOrThrow("control_name")),
                cur.getString(cur.getColumnIndexOrThrow("source")),
                cur.getString(cur.getColumnIndexOrThrow("statement")),
                cur.getString(cur.getColumnIndexOrThrow("observed_at")),
                cur.getLong(cur.getColumnIndexOrThrow("created_at"))
            )
        }
        result
    }

    fun listDecisions(): List<Decision> = readableDatabase.use { db ->
        val result = mutableListOf<Decision>()
        db.rawQuery("SELECT * FROM decisions ORDER BY CASE status WHEN 'PENDING' THEN 0 ELSE 1 END, id DESC", null).use { cur ->
            while (cur.moveToNext()) result += Decision(
                cur.getLong(cur.getColumnIndexOrThrow("id")),
                cur.getString(cur.getColumnIndexOrThrow("title")),
                cur.getString(cur.getColumnIndexOrThrow("details")),
                cur.getString(cur.getColumnIndexOrThrow("risk")),
                cur.getInt(cur.getColumnIndexOrThrow("required_approvals")),
                cur.getString(cur.getColumnIndexOrThrow("status")),
                cur.getLong(cur.getColumnIndexOrThrow("created_at")),
                if (cur.isNull(cur.getColumnIndexOrThrow("decided_at"))) null else cur.getLong(cur.getColumnIndexOrThrow("decided_at")),
                cur.getString(cur.getColumnIndexOrThrow("decided_by"))
            )
        }
        result
    }

    fun listAudit(): List<AuditEvent> = readableDatabase.use { db ->
        val result = mutableListOf<AuditEvent>()
        db.rawQuery("SELECT * FROM audit ORDER BY id DESC", null).use { cur ->
            while (cur.moveToNext()) result += AuditEvent(
                cur.getLong(cur.getColumnIndexOrThrow("id")),
                cur.getString(cur.getColumnIndexOrThrow("action")),
                cur.getString(cur.getColumnIndexOrThrow("object_type")),
                if (cur.isNull(cur.getColumnIndexOrThrow("object_id"))) null else cur.getLong(cur.getColumnIndexOrThrow("object_id")),
                cur.getString(cur.getColumnIndexOrThrow("payload")),
                cur.getString(cur.getColumnIndexOrThrow("prev_hash")),
                cur.getString(cur.getColumnIndexOrThrow("hash")),
                cur.getLong(cur.getColumnIndexOrThrow("created_at"))
            )
        }
        result
    }

    @Synchronized fun createControl(name: String, requirement: String, threshold: Int): Long {
        require(name.isNotBlank() && requirement.isNotBlank() && threshold >= 1)
        val db = writableDatabase
        val now = System.currentTimeMillis()
        val id = db.insertOrThrow("controls", null, cv("name" to name.trim(), "requirement" to requirement.trim(), "threshold" to threshold, "created_at" to now))
        appendAudit(db, "control.created", "control", id, JSONObject().put("name", name.trim()).put("requirement", requirement.trim()).put("threshold", threshold))
        return id
    }

    @Synchronized fun addEvidence(controlId: Long, source: String, statement: String, observedAt: String): Long {
        require(source.isNotBlank() && statement.isNotBlank() && observedAt.isNotBlank())
        val db = writableDatabase
        db.rawQuery("SELECT id FROM controls WHERE id=?", arrayOf(controlId.toString())).use { if (!it.moveToFirst()) error("Control not found") }
        val now = System.currentTimeMillis()
        val id = db.insertOrThrow("evidence", null, cv("control_id" to controlId, "source" to source.trim(), "statement" to statement.trim(), "observed_at" to observedAt.trim(), "created_at" to now))
        appendAudit(db, "evidence.created", "evidence", id, JSONObject().put("control_id", controlId).put("source", source.trim()).put("statement", statement.trim()).put("observed_at", observedAt.trim()))
        return id
    }

    @Synchronized fun runCheck(controlId: Long): String {
        val db = writableDatabase
        var threshold = -1
        db.rawQuery("SELECT threshold FROM controls WHERE id=?", arrayOf(controlId.toString())).use { if (it.moveToFirst()) threshold = it.getInt(0) }
        if (threshold < 0) error("Control not found")
        val evidenceCount = db.rawQuery("SELECT COUNT(*) FROM evidence WHERE control_id=?", arrayOf(controlId.toString())).use { it.moveToFirst(); it.getInt(0) }
        val status = if (evidenceCount >= threshold) "PASS" else "INSUFFICIENT_EVIDENCE"
        val id = db.insertOrThrow("checks", null, cv("control_id" to controlId, "status" to status, "evidence_count" to evidenceCount, "created_at" to System.currentTimeMillis()))
        appendAudit(db, "check.run", "check", id, JSONObject().put("control_id", controlId).put("status", status).put("evidence_count", evidenceCount))
        return status
    }

    @Synchronized fun createDecision(title: String, details: String, risk: String): Long {
        val requiredApprovals = 1
        require(title.isNotBlank() && details.isNotBlank())
        val db = writableDatabase
        val now = System.currentTimeMillis()
        val id = db.insertOrThrow("decisions", null, cv("title" to title.trim(), "details" to details.trim(), "risk" to risk, "required_approvals" to requiredApprovals, "status" to "PENDING", "created_at" to now))
        appendAudit(db, "decision.created", "decision", id, JSONObject().put("title", title.trim()).put("risk", risk).put("required_approvals", requiredApprovals))
        return id
    }

    @Synchronized fun decide(id: Long, approve: Boolean, actor: String): String {
        val db = writableDatabase
        val status = if (approve) "APPROVED" else "REJECTED"
        val updated = db.update("decisions", cv("status" to status, "decided_at" to System.currentTimeMillis(), "decided_by" to actor.trim().ifBlank { "Local user" }), "id=? AND status='PENDING'", arrayOf(id.toString()))
        if (updated != 1) error("Decision is missing or already decided")
        appendAudit(db, "decision.$status".lowercase(), "decision", id, JSONObject().put("status", status).put("actor", actor.trim().ifBlank { "Local user" }))
        return status
    }

    fun exportJson(): String = readableDatabase.use { db ->
        val root = JSONObject().put("format", "proofrail-workspace").put("schemaVersion", 1)
        root.put("controls", queryArray(db, "SELECT * FROM controls ORDER BY id"))
        root.put("evidence", queryArray(db, "SELECT * FROM evidence ORDER BY id"))
        root.put("checks", queryArray(db, "SELECT * FROM checks ORDER BY id"))
        root.put("decisions", queryArray(db, "SELECT * FROM decisions ORDER BY id"))
        root.put("audit", queryArray(db, "SELECT * FROM audit ORDER BY id"))
        root.toString(2)
    }

    @Synchronized fun importJson(raw: String) {
        val root = JSONObject(raw)
        require(root.optString("format") == "proofrail-workspace") { "Invalid ProofRail backup" }
        require(root.optInt("schemaVersion") == 1) { "Unsupported backup schema" }
        val db = writableDatabase
        db.beginTransaction()
        try {
            db.delete("audit", null, null)
            db.delete("checks", null, null)
            db.delete("evidence", null, null)
            db.delete("decisions", null, null)
            db.delete("controls", null, null)

            importRows(db, root.getJSONArray("controls"), "controls") { o -> cv("id" to o.getLong("id"), "name" to o.getString("name"), "requirement" to o.getString("requirement"), "threshold" to o.getInt("threshold"), "created_at" to o.getLong("created_at")) }
            importRows(db, root.getJSONArray("evidence"), "evidence") { o -> cv("id" to o.getLong("id"), "control_id" to o.getLong("control_id"), "source" to o.getString("source"), "statement" to o.getString("statement"), "observed_at" to o.getString("observed_at"), "created_at" to o.getLong("created_at")) }
            importRows(db, root.getJSONArray("checks"), "checks") { o -> cv("id" to o.getLong("id"), "control_id" to o.getLong("control_id"), "status" to o.getString("status"), "evidence_count" to o.getInt("evidence_count"), "created_at" to o.getLong("created_at")) }
            importRows(db, root.getJSONArray("decisions"), "decisions") { o -> cv("id" to o.getLong("id"), "title" to o.getString("title"), "details" to o.getString("details"), "risk" to o.getString("risk"), "required_approvals" to o.getInt("required_approvals"), "status" to o.getString("status"), "created_at" to o.getLong("created_at"), "decided_at" to if (o.isNull("decided_at")) null else o.getLong("decided_at"), "decided_by" to if (o.isNull("decided_by")) null else o.getString("decided_by")) }
            importRows(db, root.getJSONArray("audit"), "audit") { o -> cv("id" to o.getLong("id"), "action" to o.getString("action"), "object_type" to o.getString("object_type"), "object_id" to if (o.isNull("object_id")) null else o.getLong("object_id"), "payload" to o.getString("payload"), "prev_hash" to o.getString("prev_hash"), "hash" to o.getString("hash"), "created_at" to o.getLong("created_at")) }

            val verification = verifyChain(db)
            require(verification.valid) { "Backup audit chain is invalid" }
            db.setTransactionSuccessful()
        } finally {
            db.endTransaction()
        }
    }

    fun verifyAudit(): ChainVerification = readableDatabase.use(::verifyChain)

    private fun verifyChain(db: SQLiteDatabase): ChainVerification {
        var prev = GENESIS
        var entries = 0
        db.rawQuery("SELECT * FROM audit ORDER BY id", null).use { cur ->
            while (cur.moveToNext()) {
                entries++
                val id = cur.getLong(cur.getColumnIndexOrThrow("id"))
                val action = cur.getString(cur.getColumnIndexOrThrow("action"))
                val objectType = cur.getString(cur.getColumnIndexOrThrow("object_type"))
                val objectId = if (cur.isNull(cur.getColumnIndexOrThrow("object_id"))) "null" else cur.getLong(cur.getColumnIndexOrThrow("object_id")).toString()
                val payload = cur.getString(cur.getColumnIndexOrThrow("payload"))
                val actualPrev = cur.getString(cur.getColumnIndexOrThrow("prev_hash"))
                val actualHash = cur.getString(cur.getColumnIndexOrThrow("hash"))
                val expected = digest(action, objectType, objectId, payload, prev)
                if (actualPrev != prev || actualHash != expected) return ChainVerification(false, entries, id)
                prev = actualHash
            }
        }
        return ChainVerification(true, entries)
    }

    private fun appendAudit(db: SQLiteDatabase, action: String, objectType: String, objectId: Long?, payload: JSONObject) {
        val prev = db.rawQuery("SELECT hash FROM audit ORDER BY id DESC LIMIT 1", null).use { if (it.moveToFirst()) it.getString(0) else GENESIS }
        val payloadText = payload.toString()
        val objectIdText = objectId?.toString() ?: "null"
        val hash = digest(action, objectType, objectIdText, payloadText, prev)
        db.insertOrThrow("audit", null, cv("action" to action, "object_type" to objectType, "object_id" to objectId, "payload" to payloadText, "prev_hash" to prev, "hash" to hash, "created_at" to System.currentTimeMillis()))
    }

    private fun digest(action: String, objectType: String, objectId: String, payload: String, prev: String): String {
        val input = listOf(action, objectType, objectId, payload, prev).joinToString("|")
        return MessageDigest.getInstance("SHA-256").digest(input.toByteArray()).joinToString("") { "%02x".format(it) }
    }

    private fun count(db: SQLiteDatabase, table: String): Int = db.rawQuery("SELECT COUNT(*) FROM $table", null).use { it.moveToFirst(); it.getInt(0) }

    private fun cv(vararg items: Pair<String, Any?>): ContentValues = ContentValues().apply {
        items.forEach { (key, value) -> when (value) {
            null -> putNull(key)
            is String -> put(key, value)
            is Int -> put(key, value)
            is Long -> put(key, value)
            is Boolean -> put(key, if (value) 1 else 0)
            else -> put(key, value.toString())
        }}
    }

    private fun queryArray(db: SQLiteDatabase, sql: String): JSONArray {
        val array = JSONArray()
        db.rawQuery(sql, null).use { cur ->
            while (cur.moveToNext()) {
                val row = JSONObject()
                for (i in 0 until cur.columnCount) {
                    val name = cur.getColumnName(i)
                    if (cur.isNull(i)) row.put(name, JSONObject.NULL) else when (cur.getType(i)) {
                        1 -> row.put(name, cur.getLong(i))
                        2 -> row.put(name, cur.getDouble(i))
                        else -> row.put(name, cur.getString(i))
                    }
                }
                array.put(row)
            }
        }
        return array
    }

    private fun importRows(db: SQLiteDatabase, array: JSONArray, table: String, values: (JSONObject) -> ContentValues) {
        for (i in 0 until array.length()) db.insertOrThrow(table, null, values(array.getJSONObject(i)))
    }
}
