package com.proofrail.app

import android.content.Context
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.background
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.FactCheck
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.TaskAlt
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Divider
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SmallTopAppBar
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.platform.LocalContext
import com.proofrail.app.data.Control
import com.proofrail.app.data.Decision
import com.proofrail.app.data.Evidence
import com.proofrail.app.data.ProofDatabase
import com.proofrail.app.data.DashboardState

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { ProofRailThemeRoot() }
    }
}

private enum class Tab(val label: String) {
    OVERVIEW("Overview"), CONTROLS("Controls"), EVIDENCE("Evidence"), DECISIONS("Decisions"), AUDIT("Audit")
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ProofRailThemeRoot() {
    com.proofrail.app.ui.theme.ProofRailTheme {
        val context = LocalContext.current
        val db = remember { ProofDatabase(context) }
        var tab by remember { mutableStateOf(Tab.OVERVIEW) }
        var refresh by remember { mutableStateOf(0) }
        var settings by remember { mutableStateOf(false) }
        var toast by remember { mutableStateOf<String?>(null) }
        val snackbar = remember { SnackbarHostState() }
        val dashboard = remember(refresh) { db.dashboard() }

        val export = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("application/json")) { uri: Uri? ->
            if (uri != null) {
                try {
                    context.contentResolver.openOutputStream(uri)?.use { it.write(db.exportJson().toByteArray()) }
                    toast = "Backup exported"
                } catch (e: Exception) { toast = e.message ?: "Export failed" }
            }
        }
        val import = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
            if (uri != null) {
                try {
                    val data = context.contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
                    if (data == null) error("Unable to read backup")
                    db.importJson(data)
                    refresh++
                    toast = "Backup restored"
                } catch (e: Exception) { toast = e.message ?: "Import failed" }
            }
        }

        LaunchedEffect(toast) {
            toast?.let { snackbar.showSnackbar(it); toast = null }
        }

        Scaffold(
            snackbarHost = { SnackbarHost(snackbar) },
            topBar = {
                SmallTopAppBar(
                    title = { Brand() },
                    actions = { IconButton({ settings = true }) { Icon(Icons.Filled.Settings, "Settings") } },
                    colors = TopAppBarDefaults.smallTopAppBarColors(containerColor = Color.White)
                )
            },
            bottomBar = {
                NavigationBar {
                    Tab.entries.forEach { t ->
                        NavigationBarItem(t == tab, { tab = t }, icon = { TabIcon(t) }, label = { Text(t.label, fontSize = 10.sp) })
                    }
                }
            },
            floatingActionButton = {
                if (tab == Tab.CONTROLS || tab == Tab.EVIDENCE || tab == Tab.DECISIONS) {
                    FloatingActionButton({
                        when (tab) {
                            Tab.CONTROLS -> tab = Tab.CONTROLS
                            Tab.EVIDENCE -> tab = Tab.EVIDENCE
                            Tab.DECISIONS -> tab = Tab.DECISIONS
                            else -> Unit
                        }
                    }) { Icon(Icons.Filled.Add, "Create") }
                }
            },
            containerColor = MaterialTheme.colorScheme.background
        ) { padding ->
            when (tab) {
                Tab.OVERVIEW -> Overview(padding, dashboard, { tab = it })
                Tab.CONTROLS -> Controls(padding, db, { refresh++ })
                Tab.EVIDENCE -> EvidenceScreen(padding, db, { refresh++ })
                Tab.DECISIONS -> Decisions(padding, db, { refresh++ })
                Tab.AUDIT -> Audit(padding, db)
            }
        }

        if (settings) {
            SettingsDialog(
                onDismiss = { settings = false },
                onExport = { export.launch("proofrail-workspace.json") },
                onImport = { import.launch(arrayOf("application/json", "text/plain")) },
                onErase = { context.deleteDatabase("proofrail.db"); refresh++; settings = false; toast = "Local workspace erased" }
            )
        }
    }
}

@Composable private fun Brand() {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(30.dp).background(Color(0xFF2878FF), RoundedCornerShape(9.dp)), contentAlignment = Alignment.Center) {
            Icon(Icons.Filled.Shield, null, tint = Color.White, modifier = Modifier.size(18.dp))
        }
        Spacer(Modifier.width(9.dp))
        Text("ProofRail", fontWeight = FontWeight.ExtraBold, fontSize = 20.sp)
    }
}

@Composable private fun TabIcon(tab: Tab) {
    val icon = when (tab) {
        Tab.OVERVIEW -> Icons.Filled.Home
        Tab.CONTROLS -> Icons.Filled.FactCheck
        Tab.EVIDENCE -> Icons.Filled.Description
        Tab.DECISIONS -> Icons.Filled.TaskAlt
        Tab.AUDIT -> Icons.Filled.Lock
    }
    Icon(icon, null)
}

@Composable private fun Overview(padding: androidx.compose.foundation.layout.PaddingValues, d: DashboardState, nav: (Tab) -> Unit) {
    LazyColumn(Modifier.fillMaxSize().padding(padding).padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item {
            Text("Proof, not promises.", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.ExtraBold)
            Text("Evidence, decisions and audit integrity — stored on this device.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        item {
            Card(shape = RoundedCornerShape(20.dp), colors = CardDefaults.cardColors(containerColor = if (d.auditValid) Color(0xFFEAF7F0) else Color(0xFFFFECEA))) {
                Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(if (d.auditValid) Icons.Filled.CheckCircle else Icons.Filled.Shield, null, tint = if (d.auditValid) Color(0xFF17784B) else Color(0xFFB42318))
                    Spacer(Modifier.width(10.dp))
                    Column {
                        Text(if (d.auditValid) "Audit chain verified" else "Audit chain needs review", fontWeight = FontWeight.Bold)
                        Text(d.auditEntries.toString() + " events", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Metric("Controls", d.controls, Icons.Filled.FactCheck, { nav(Tab.CONTROLS) }, Modifier.weight(1f))
                Metric("Evidence", d.evidence, Icons.Filled.Description, { nav(Tab.EVIDENCE) }, Modifier.weight(1f))
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Metric("Checks", d.checks, Icons.Filled.CheckCircle, { nav(Tab.CONTROLS) }, Modifier.weight(1f))
                Metric("Pending", d.decisionsPending, Icons.Filled.TaskAlt, { nav(Tab.DECISIONS) }, Modifier.weight(1f))
            }
        }
        item {
            Card(shape = RoundedCornerShape(20.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
                Column(Modifier.padding(18.dp)) {
                    Text("How ProofRail works", fontWeight = FontWeight.Bold, fontSize = 17.sp)
                    Text("Capture evidence → run deterministic checks → record decisions → verify the audit chain.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

@Composable private fun Metric(title: String, value: Int, icon: androidx.compose.ui.graphics.vector.ImageVector, click: () -> Unit, modifier: Modifier) {
    Card(onClick = click, modifier = modifier, shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
        Column(Modifier.padding(16.dp)) {
            Icon(icon, null, tint = Color(0xFF2878FF))
            Spacer(Modifier.height(9.dp))
            Text(value.toString(), fontWeight = FontWeight.ExtraBold, fontSize = 27.sp)
            Text(title, color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 12.sp)
        }
    }
}

@Composable private fun Controls(padding: androidx.compose.foundation.layout.PaddingValues, db: ProofDatabase, changed: () -> Unit) {
    var controls by remember { mutableStateOf(db.listControls()) }
    var create by remember { mutableStateOf(false) }
    fun reload() { controls = db.listControls(); changed() }
    Box(Modifier.fillMaxSize().padding(padding)) {
        if (controls.isEmpty()) Empty("No controls yet", "Create a control with an evidence threshold.") { create = true }
        else LazyColumn(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item { Text("Controls", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.ExtraBold); Text("Deterministic checks against captured evidence.", color = MaterialTheme.colorScheme.onSurfaceVariant) }
            items(controls, key = { it.id }) { c ->
                Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
                    Column(Modifier.padding(17.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(c.name, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            Status(c.latestStatus ?: "NOT CHECKED")
                        }
                        Spacer(Modifier.height(7.dp))
                        Text(c.requirement, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(Modifier.height(12.dp))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Evidence " + (c.latestEvidenceCount ?: 0) + "/" + c.threshold, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Spacer(Modifier.weight(1f))
                            Button({ db.runCheck(c.id); reload() }) { Text("Run check") }
                        }
                    }
                }
            }
        }
    }
    if (create) {
        CreateControl({ create = false }) { name, req, threshold -> db.createControl(name, req, threshold); create = false; reload() }
    }
}

@Composable private fun EvidenceScreen(padding: androidx.compose.foundation.layout.PaddingValues, db: ProofDatabase, changed: () -> Unit) {
    var controls by remember { mutableStateOf(db.listControls()) }
    var evidence by remember { mutableStateOf(db.listEvidence()) }
    var create by remember { mutableStateOf(false) }
    fun reload() { controls = db.listControls(); evidence = db.listEvidence(); changed() }
    Box(Modifier.fillMaxSize().padding(padding)) {
        if (evidence.isEmpty()) Empty("No evidence captured", "Capture a source-backed observation and attach it to a control.") { if (controls.isNotEmpty()) create = true }
        else LazyColumn(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item { Text("Evidence", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.ExtraBold); Text("Records stored locally and linked to controls.", color = MaterialTheme.colorScheme.onSurfaceVariant) }
            items(evidence, key = { it.id }) { e -> EvidenceCard(e) }
        }
    }
    if (create) CreateEvidence(controls, { create = false }) { cid, source, statement, observed -> db.addEvidence(cid, source, statement, observed); create = false; reload() }
}

@Composable private fun EvidenceCard(e: Evidence) {
    Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
        Column(Modifier.padding(17.dp)) {
            Row { Text(e.controlName, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f)); Text(e.observedAt, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant) }
            Spacer(Modifier.height(7.dp)); Text(e.statement, fontSize = 14.sp); Spacer(Modifier.height(7.dp))
            Text("Source · " + e.source, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable private fun Decisions(padding: androidx.compose.foundation.layout.PaddingValues, db: ProofDatabase, changed: () -> Unit) {
    var list by remember { mutableStateOf(db.listDecisions()) }
    var create by remember { mutableStateOf(false) }
    fun reload() { list = db.listDecisions(); changed() }
    Box(Modifier.fillMaxSize().padding(padding)) {
        if (list.isEmpty()) Empty("No decisions", "Create a decision gate when a sensitive action requires an explicit approval.") { create = true }
        else LazyColumn(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item { Text("Decision gate", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.ExtraBold); Text("Human decisions are explicit and audited.", color = MaterialTheme.colorScheme.onSurfaceVariant) }
            items(list, key = { it.id }) { d ->
                Card(shape = RoundedCornerShape(18.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
                    Column(Modifier.padding(17.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) { Text(d.title, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f)); Status(d.status) }
                        Spacer(Modifier.height(7.dp)); Text(d.details, fontSize = 13.sp)
                        Spacer(Modifier.height(10.dp))
                        if (d.status == "PENDING") Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton({ db.decide(d.id, false, "Local user"); reload() }, Modifier.weight(1f)) { Text("Reject") }
                            Button({ db.decide(d.id, true, "Local user"); reload() }, Modifier.weight(1f)) { Text("Approve") }
                        } else Text(d.status + " · " + (d.decidedBy ?: "Local user"), fontWeight = FontWeight.SemiBold)
                    }
                }
            }
        }
    }
    if (create) CreateDecision({ create = false }) { title, details, risk -> db.createDecision(title, details, risk); create = false; reload() }
}

@Composable private fun Audit(padding: androidx.compose.foundation.layout.PaddingValues, db: ProofDatabase) {
    val verification = db.verifyAudit()
    val events = db.listAudit()
    LazyColumn(Modifier.fillMaxSize().padding(padding).padding(20.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        item { Text("Audit", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.ExtraBold); Text("SHA-256 chained records can be verified on-device.", color = MaterialTheme.colorScheme.onSurfaceVariant) }
        item { Card(colors = CardDefaults.cardColors(containerColor = if (verification.valid) Color(0xFFEAF7F0) else Color(0xFFFFECEA)), shape = RoundedCornerShape(18.dp)) { Text((if (verification.valid) "VALID" else "BROKEN") + " · " + verification.entries + " entries", Modifier.padding(16.dp), fontWeight = FontWeight.Bold) } }
        if (events.isEmpty()) item { Text("No events yet.", color = MaterialTheme.colorScheme.onSurfaceVariant) }
        items(events, key = { it.id }) { e ->
            Card(shape = RoundedCornerShape(16.dp), colors = CardDefaults.cardColors(containerColor = Color.White)) {
                Column(Modifier.padding(15.dp)) {
                    Row { Text(e.action, fontWeight = FontWeight.SemiBold, modifier = Modifier.weight(1f)); Text("#" + e.id, fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant) }
                    Spacer(Modifier.height(4.dp)); Text(e.objectType, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text("hash " + e.hash.take(18) + "…", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}

@Composable private fun Status(text: String) {
    Text(text, Modifier.background(if (text == "PASS" || text == "APPROVED" || text == "VALID") Color(0xFFE7F6ED) else Color(0xFFFFF1D8), RoundedCornerShape(50)).padding(horizontal = 8.dp, vertical = 5.dp), fontSize = 10.sp, fontWeight = FontWeight.Bold)
}

@Composable private fun Empty(title: String, body: String, action: (() -> Unit)) {
    Box(Modifier.fillMaxSize().padding(30.dp), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) { Icon(Icons.Filled.Shield, null, tint = Color(0xFF2878FF), modifier = Modifier.size(48.dp)); Spacer(Modifier.height(12.dp)); Text(title, fontWeight = FontWeight.Bold, fontSize = 19.sp); Spacer(Modifier.height(6.dp)); Text(body, color = MaterialTheme.colorScheme.onSurfaceVariant); Spacer(Modifier.height(14.dp)); Button(action) { Text("Create") } }
    }
}

@Composable private fun CreateControl(cancel: () -> Unit, create: (String, String, Int) -> Unit) {
    var name by remember { mutableStateOf("") }; var req by remember { mutableStateOf("") }; var threshold by remember { mutableStateOf("1") }
    AlertDialog({ cancel() }, title = { Text("New control") }, text = { Column(verticalArrangement = Arrangement.spacedBy(9.dp)) {
        OutlinedTextField(name, { name = it }, label = { Text("Name") }, singleLine = true)
        OutlinedTextField(req, { req = it }, label = { Text("Requirement") }, minLines = 3)
        OutlinedTextField(threshold, { threshold = it.filter(Char::isDigit).take(3) }, label = { Text("Evidence threshold") }, singleLine = true)
    }}, confirmButton = { Button({ threshold.toIntOrNull()?.let { if (name.isNotBlank() && req.isNotBlank() && it > 0) create(name, req, it) } }) { Text("Create") } }, dismissButton = { OutlinedButton({ cancel() }) { Text("Cancel") } })
}

@Composable private fun CreateEvidence(controls: List<Control>, cancel: () -> Unit, create: (Long, String, String, String) -> Unit) {
    var selected by remember { mutableStateOf(controls.firstOrNull()?.id) }; var source by remember { mutableStateOf("") }; var statement by remember { mutableStateOf("") }; var observed by remember { mutableStateOf("") }
    AlertDialog({ cancel() }, title = { Text("Add evidence") }, text = { Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        controls.forEach { c -> AssistChip(onClick = { selected = c.id }, label = { Text(if (selected == c.id) "✓ " + c.name else c.name) }) }
        OutlinedTextField(source, { source = it }, label = { Text("Source") }, singleLine = true)
        OutlinedTextField(statement, { statement = it }, label = { Text("Statement") }, minLines = 3)
        OutlinedTextField(observed, { observed = it }, label = { Text("Observed at (ISO 8601)") }, singleLine = true)
    }}, confirmButton = { Button({ if (selected != null && source.isNotBlank() && statement.isNotBlank() && observed.isNotBlank()) create(selected!!, source, statement, observed) }) { Text("Capture") } }, dismissButton = { OutlinedButton({ cancel() }) { Text("Cancel") } })
}

@Composable private fun CreateDecision(cancel: () -> Unit, create: (String, String, String) -> Unit) {
    var title by remember { mutableStateOf("") }; var details by remember { mutableStateOf("") }; var risk by remember { mutableStateOf("MEDIUM") }
    AlertDialog({ cancel() }, title = { Text("New decision request") }, text = { Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedTextField(title, { title = it }, label = { Text("Action") }, singleLine = true)
        OutlinedTextField(details, { details = it }, label = { Text("Context") }, minLines = 3)
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) { listOf("LOW", "MEDIUM", "HIGH").forEach { r -> AssistChip(onClick = { risk = r }, label = { Text(if (risk == r) "✓ " + r else r) }) } }
    }}, confirmButton = { Button({ if (title.isNotBlank() && details.isNotBlank()) create(title, details, risk) }) { Text("Create") } }, dismissButton = { OutlinedButton({ cancel() }) { Text("Cancel") } })
}

@Composable private fun SettingsDialog(onDismiss: () -> Unit, onExport: () -> Unit, onImport: () -> Unit, onErase: () -> Unit) {
    var confirm by remember { mutableStateOf(false) }
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Workspace") },
        text = { Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Local-first. This release has no network permission and does not upload workspace data.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            OutlinedButton(onExport, Modifier.fillMaxWidth()) { Text("Export JSON backup") }
            OutlinedButton(onImport, Modifier.fillMaxWidth()) { Text("Restore JSON backup") }
            Divider()
            OutlinedButton({ confirm = true }, Modifier.fillMaxWidth()) { Text("Erase local workspace") }
        }},
        confirmButton = { OutlinedButton(onDismiss) { Text("Close") } }
    )
    if (confirm) AlertDialog(onDismissRequest = { confirm = false }, title = { Text("Erase workspace?") }, text = { Text("This permanently deletes the local database.") }, confirmButton = { Button({ confirm = false; onErase() }) { Text("Erase") } }, dismissButton = { OutlinedButton({ confirm = false }) { Text("Cancel") } })
}
