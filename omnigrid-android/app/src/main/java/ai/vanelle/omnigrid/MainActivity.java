package ai.vanelle.omnigrid;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import java.util.ArrayList;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {
    private static final int BG=Color.rgb(7,17,31), PANEL=Color.rgb(16,31,51), WHITE=Color.rgb(239,246,255), MUTED=Color.rgb(160,180,203), CYAN=Color.rgb(88,214,255), BLUE=Color.rgb(40,112,235), RED=Color.rgb(255,135,135), GREEN=Color.rgb(112,235,173);
    private final ExecutorService executor=Executors.newSingleThreadExecutor();
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final ArrayList<Task> tasks=new ArrayList<>();
    private LinearLayout root,feed;
    private EditText prompt;
    private TextView status,modelStatus;
    private boolean receiverRegistered=false;
    private final Runnable pollDownload=new Runnable(){@Override public void run(){if(modelStatus!=null){modelStatus.setText(LocalModelManager.downloadStatus(MainActivity.this));handler.postDelayed(this,2500);}}};
    private final BroadcastReceiver downloadReceiver=new BroadcastReceiver(){@Override public void onReceive(Context context, Intent intent){
        if(DownloadManager.ACTION_DOWNLOAD_COMPLETE.equals(intent.getAction()) && intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID,-2L)==LocalModelManager.savedDownloadId(MainActivity.this)){
            status.setText("VÉRIFICATION DU MODÈLE…");
            executor.execute(()->{boolean ok=false;String message;
                try{ok=LocalModelManager.verifyIntegrity(MainActivity.this);message=ok?"Modèle local vérifié. Test d'inférence…":"Échec de vérification SHA-256 : modèle rejeté.";}
                catch(Exception e){message="Vérification impossible : "+e.getMessage();}
                final boolean valid=ok;final String result=message;
                runOnUiThread(()->{modelStatus.setText(result);status.setText(valid?"IA LOCALE PRÊTE":"MODÈLE INVALIDE");if(valid)runLocalSelfTest();});
            });
        }
    }};
    private static final class Task { final String request; String state,result; Task(String r,String s){request=r;state=s;} }
    @Override public void onCreate(Bundle state){super.onCreate(state);buildHome();IntentFilter f=new IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE);if(android.os.Build.VERSION.SDK_INT>=33)registerReceiver(downloadReceiver,f,Context.RECEIVER_NOT_EXPORTED);else registerReceiver(downloadReceiver,f);receiverRegistered=true;handler.post(pollDownload);if(LocalModelManager.isPresent(this)){status.setText("VÉRIFICATION DU MODÈLE LOCAL…");executor.execute(()->{try{boolean valid=LocalModelManager.verifyIntegrity(MainActivity.this);runOnUiThread(()->{status.setText(valid?"IA LOCALE PRÊTE":"MODÈLE LOCAL INVALIDE");modelStatus.setText(valid?"Modèle vérifié — prêt hors ligne":"Le modèle a échoué à la vérification SHA-256.");});}catch(Exception e){runOnUiThread(()->{status.setText("VÉRIFICATION IMPOSSIBLE");modelStatus.setText(e.getMessage());});}});}}
    private GradientDrawable shape(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(radius);d.setStroke(1,Color.rgb(39,62,88));return d;}
    private TextView text(String value,int size,int color,boolean bold){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(color);t.setPadding(0,4,0,4);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
    private Button button(String value,Runnable action){Button b=new Button(this);b.setText(value);b.setTextColor(WHITE);b.setAllCaps(false);b.setBackground(shape(BLUE,18));b.setOnClickListener(v->action.run());return b;}
    private EditText field(String hint,boolean multi){EditText e=new EditText(this);e.setHint(hint);e.setTextColor(WHITE);e.setHintTextColor(MUTED);e.setTextSize(15);e.setPadding(14,10,14,10);e.setBackground(shape(PANEL,14));if(multi){e.setMinLines(3);e.setGravity(Gravity.TOP|Gravity.START);e.setSingleLine(false);}else e.setSingleLine(true);return e;}
    private LinearLayout column(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);return l;}
    private void gap(LinearLayout l,int h){l.addView(new View(this),new LinearLayout.LayoutParams(1,h));}
    private void buildHome(){
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(BG);root=column();root.setPadding(18,20,18,28);scroll.addView(root);setContentView(scroll);
        root.addView(text("VANELLE",14,CYAN,true));root.addView(text("OMNIGRID AI",30,WHITE,true));root.addView(text("IA locale • privée • hors ligne après téléchargement",13,MUTED,false));gap(root,12);
        LinearLayout panel=column();panel.setPadding(14,12,14,12);panel.setBackground(shape(PANEL,18));status=text("INITIALISATION DU MOTEUR LOCAL…",14,CYAN,true);panel.addView(status);panel.addView(text("Les demandes sont traitées sur ce téléphone. Aucun prompt ni aucune clé API n'est envoyé à un fournisseur distant.",12,MUTED,false));root.addView(panel);
        gap(root,14);root.addView(text("Moteur IA local",20,WHITE,true));LinearLayout modelCard=column();modelCard.setPadding(14,12,14,12);modelCard.setBackground(shape(PANEL,18));
        modelCard.addView(text("Qwen2.5 0.5B Instruct • GGUF Q4_0 • environ 429 Mo",14,WHITE,true));
        modelCard.addView(text("Le premier téléchargement nécessite Internet. Ensuite, la génération de texte fonctionne hors ligne. Prévois au moins 1,5 Go de mémoire libre pour le modèle et le cache.",12,MUTED,false));
        modelStatus=text(LocalModelManager.downloadStatus(this),13,CYAN,true);modelCard.addView(modelStatus);gap(modelCard,8);
        modelCard.addView(button("Télécharger / réinstaller le modèle local",this::confirmDownload));modelCard.addView(button("Tester réellement l'IA locale",this::runLocalSelfTest));root.addView(modelCard);
        gap(root,16);root.addView(text("Outils locaux exécutables",20,WHITE,true));LinearLayout tools=column();tools.setPadding(14,12,14,12);tools.setBackground(shape(PANEL,18));tools.addView(text("Ces commandes agissent réellement sur cet appareil, sans Internet ni modèle IA :",13,GREEN,true));tools.addView(text(LocalToolbox.help(),12,MUTED,false));root.addView(tools);gap(root,16);root.addView(text("Nouvelle tâche",20,WHITE,true));prompt=field("Ex. calc: (12 + 3) * 4 ou note: idées du projet",true);root.addView(prompt);gap(root,8);root.addView(button("Exécuter l’outil local ou analyser avec l’IA",this::submitTask));gap(root,16);
        root.addView(text("Contrôle et limites",20,WHITE,true));LinearLayout catalog=column();catalog.setPadding(14,12,14,12);catalog.setBackground(shape(PANEL,18));
        catalog.addView(text("• Exécution du modèle sur l'appareil avec llama.cpp",14,GREEN,false));catalog.addView(text("• Téléchargement initial géré par Android, reprenable selon le système et le réseau",12,MUTED,false));catalog.addView(text("• Les commandes calc:, note:, notes:list, time:now et device:info sont exécutées localement",12,GREEN,false));catalog.addView(text("• Pas encore de contrôle distant Windows/Linux/macOS : il faut des agents installés sur ces ordinateurs et un canal sécurisé",12,RED,false));catalog.addView(text("• Un seul modèle GGUF est configuré et vérifié dans cette version ; ajouter d’autres modèles exige leurs fichiers, licences, empreintes et tests de compatibilité",12,MUTED,false));root.addView(catalog);
        gap(root,16);root.addView(text("Journal de cette session",20,WHITE,true));feed=column();root.addView(feed);renderTasks();
    }
    private void confirmDownload(){
        new AlertDialog.Builder(this).setTitle("Installer l'IA locale").setMessage("Télécharger Qwen2.5 0.5B Instruct (~429 Mo) depuis Hugging Face ? Après vérification SHA-256, les prompts seront traités sur l'appareil sans Internet.")
            .setNegativeButton("Annuler",null).setPositiveButton("Télécharger",(d,w)->{
                try{long id=LocalModelManager.startDownload(this);modelStatus.setText("Téléchargement lancé (ID "+id+"). Garde un espace libre suffisant.");status.setText("TÉLÉCHARGEMENT DU MODÈLE");}
                catch(Exception e){toast("Impossible de démarrer : "+e.getMessage());}
            }).show();
    }
    private boolean needsApproval(String s){
        String x=s.toLowerCase(Locale.ROOT);String[] terms={"supprimer","effacer","delete","format","payer","payment","achat","acheter","envoyer un email","send email","publier","publish","installer","désinstaller","shutdown","arrêter le serveur","mot de passe","password","clé privée","private key","virement","transférer de l'argent"};
        for(String term:terms)if(x.contains(term))return true;return false;
    }
    private void submitTask(){
        String request=prompt.getText().toString().trim();if(request.isEmpty()){toast("Décris d'abord la tâche.");return;}
        ((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(prompt.getWindowToken(),0);
        Task task=new Task(request,needsApproval(request)?"awaiting_approval":"queued");tasks.add(0,task);prompt.setText("");renderTasks();
        if(task.state.equals("awaiting_approval"))new AlertDialog.Builder(this).setTitle("Confirmation requise").setMessage("Cette demande semble sensible. Autorises-tu seulement son analyse par le modèle local ? Aucun accès externe n'est accordé.")
            .setNegativeButton("Refuser",(d,w)->{task.state="rejected";task.result="Refusée par l'utilisateur.";renderTasks();}).setPositiveButton("Autoriser l'analyse locale",(d,w)->routeTask(task)).show();
        else routeTask(task);
    }
    private void routeTask(Task task){
        if(LocalToolbox.handles(task.request)){
            task.state="running";task.result="Outil local en cours…";renderTasks();
            executor.execute(()->{try{String result=LocalToolbox.run(MainActivity.this,task.request);runOnUiThread(()->{task.state="completed";task.result=result;status.setText("OUTIL LOCAL EXÉCUTÉ • sans Internet");renderTasks();});}
                catch(Exception e){runOnUiThread(()->{task.state="failed";task.result=e.getMessage()==null?"Erreur de l'outil local":e.getMessage();renderTasks();});}});
            return;
        }
        execute(task);
    }
    private void execute(Task task){
        if(!LocalModelManager.isVerified(this)){task.state="failed";task.result="Le modèle local n'est pas téléchargé. Utilise « Télécharger / réinstaller le modèle local ».";renderTasks();return;}
        task.state="running";task.result="Inférence locale en cours…";renderTasks();status.setText("INFÉRENCE LOCALE…");
        executor.execute(()->{try{
            String answer=LocalInference.generate(MainActivity.this,
                "Analyse la demande suivante. Fournis : 1) objectif, 2) plan étape par étape, 3) prérequis, 4) risques et autorisations nécessaires, 5) tests de vérification. Ne prétends pas avoir réalisé une action externe.\n\nDEMANDE : "+task.request);
            runOnUiThread(()->{task.state="completed";task.result=answer;status.setText("IA LOCALE PRÊTE • hors ligne");renderTasks();});
        }catch(Exception e){runOnUiThread(()->{task.state="failed";task.result=e.getMessage()==null?"Erreur d'inférence locale":e.getMessage();status.setText("ERREUR IA LOCALE");renderTasks();});}});
    }
    private void runLocalSelfTest(){
        if(!LocalModelManager.isVerified(this)){toast("Modèle absent ou non vérifié : télécharge-le ou relance la vérification.");return;}
        status.setText("TEST RÉEL DU MODÈLE EN COURS…");modelStatus.setText("Chargement du GGUF et génération d'un texte de contrôle…");
        executor.execute(()->{try{
            String answer=LocalInference.generate(MainActivity.this,"Réponds exactement par ces mots : VANELLE IA LOCALE OK");
            boolean ok=answer.toLowerCase(Locale.ROOT).contains("vanelle");
            runOnUiThread(()->{status.setText(ok?"TEST IA LOCALE RÉUSSI":"TEST TERMINÉ — vérifier la réponse");modelStatus.setText("Réponse réelle du modèle : "+answer);toast(ok?"Inférence locale confirmée.":"Le modèle a répondu, mais le test textuel n'a pas reconnu la phrase.");});
        }catch(Exception e){runOnUiThread(()->{status.setText("TEST IA LOCALE ÉCHOUÉ");modelStatus.setText(e.getMessage());toast("Échec du test : "+e.getMessage());});}});
    }
    private void renderTasks(){
        if(feed==null)return;feed.removeAllViews();if(tasks.isEmpty()){feed.addView(text("Aucune tâche dans cette session.",13,MUTED,false));return;}
        for(Task task:tasks){LinearLayout card=column();card.setPadding(14,12,14,12);card.setBackground(shape(PANEL,16));card.addView(text(task.state.toUpperCase(Locale.ROOT).replace('_',' '),11,task.state.equals("failed")?RED:CYAN,true));card.addView(text(task.request,14,WHITE,true));
            if(task.result!=null){gap(card,5);card.addView(text(task.result,13,MUTED,false));}
            if(task.state.equals("awaiting_approval"))card.addView(button("Examiner la demande",()->new AlertDialog.Builder(this).setTitle("Autoriser cette demande ?").setMessage(task.request).setNegativeButton("Refuser",(d,w)->{task.state="rejected";task.result="Refusée.";renderTasks();}).setPositiveButton("Autoriser l'analyse locale",(d,w)->execute(task)).show()));
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=10;feed.addView(card,lp);
        }
    }
    private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
    @Override protected void onDestroy(){handler.removeCallbacks(pollDownload);if(receiverRegistered)unregisterReceiver(downloadReceiver);executor.shutdownNow();super.onDestroy();}
}
