package ai.vanelle.omnigrid;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
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
    private static final int BG=Color.rgb(7,17,31), PANEL=Color.rgb(16,31,51), WHITE=Color.rgb(239,246,255), MUTED=Color.rgb(160,180,203), CYAN=Color.rgb(88,214,255), BLUE=Color.rgb(40,112,235), RED=Color.rgb(255,135,135);
    private final ExecutorService executor=Executors.newSingleThreadExecutor();
    private final ArrayList<Task> tasks=new ArrayList<>();
    private LinearLayout root,feed;
    private EditText prompt,endpoint,model,apiKey;
    private TextView status;
    private SecurePrefs secure;
    private SharedPreferences prefs;
    private static final class Task {
        final String request; String state,result;
        Task(String r,String s){request=r;state=s;}
    }
    @Override public void onCreate(Bundle state){super.onCreate(state);secure=new SecurePrefs(this);prefs=getSharedPreferences("provider_settings",MODE_PRIVATE);buildHome();}
    private GradientDrawable shape(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(radius);d.setStroke(1,Color.rgb(39,62,88));return d;}
    private TextView text(String value,int size,int color,boolean bold){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(color);t.setPadding(0,4,0,4);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);return t;}
    private Button button(String value,Runnable action){Button b=new Button(this);b.setText(value);b.setTextColor(WHITE);b.setAllCaps(false);b.setBackground(shape(BLUE,18));b.setOnClickListener(v->action.run());return b;}
    private EditText field(String hint,String value,boolean multi){EditText e=new EditText(this);e.setHint(hint);e.setText(value);e.setTextColor(WHITE);e.setHintTextColor(MUTED);e.setTextSize(15);e.setPadding(14,10,14,10);e.setBackground(shape(PANEL,14));if(multi){e.setMinLines(3);e.setGravity(Gravity.TOP|Gravity.START);e.setSingleLine(false);}else e.setSingleLine(true);return e;}
    private LinearLayout column(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);return l;}
    private void gap(LinearLayout l,int h){l.addView(new View(this),new LinearLayout.LayoutParams(1,h));}
    private void buildHome(){
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(BG);root=column();root.setPadding(18,20,18,28);scroll.addView(root);setContentView(scroll);
        root.addView(text("VANELLE",14,CYAN,true));root.addView(text("OMNIGRID AI",30,WHITE,true));root.addView(text("Orchestration • multi-modèles • contrôle humain",13,MUTED,false));gap(root,12);
        LinearLayout panel=column();panel.setPadding(14,12,14,12);panel.setBackground(shape(PANEL,18));status=text("PRÊT • configure un fournisseur IA",14,CYAN,true);panel.addView(status);panel.addView(text("Le modèle choisi analyse et planifie. Cette version ne contrôle pas encore directement les autres ordinateurs et ne prétend pas exécuter les actions externes.",12,MUTED,false));root.addView(panel);
        gap(root,16);root.addView(text("Nouvelle tâche",20,WHITE,true));prompt=field("Décris ce que tu veux accomplir…","",true);root.addView(prompt);gap(root,8);root.addView(button("Analyser la tâche",this::submitTask));gap(root,8);root.addView(button("Paramètres IA et modèles",this::showSettings));gap(root,16);
        root.addView(text("Connecteurs",20,WHITE,true));LinearLayout catalog=column();catalog.setPadding(14,12,14,12);catalog.setBackground(shape(PANEL,18));
        catalog.addView(text("• Fournisseurs HTTPS compatibles OpenAI",14,WHITE,false));catalog.addView(text("• Identifiant de modèle configurable (selon le fournisseur et l’abonnement)",12,MUTED,false));catalog.addView(text("• Clé API chiffrée par Android Keystore",12,MUTED,false));catalog.addView(text("• Agents Windows/Linux/macOS, exécution de commandes distantes et inférence locale GGUF : non intégrés",12,RED,false));root.addView(catalog);
        gap(root,16);root.addView(text("Journal de cette session",20,WHITE,true));feed=column();root.addView(feed);renderTasks();gap(root,12);root.addView(text("Une confirmation dans cette application autorise seulement l’envoi du texte au modèle IA, pas une action irréversible sur un système externe.",12,MUTED,false));
    }
    private void showSettings(){
        LinearLayout form=column();form.setPadding(8,8,8,8);form.addView(text("URL de base HTTPS",13,MUTED,true));endpoint=field("https://api.openai.com/v1",prefs.getString("endpoint","https://api.openai.com/v1"),false);form.addView(endpoint);
        gap(form,8);form.addView(text("Identifiant exact du modèle",13,MUTED,true));model=field("ex. gpt-4o-mini",prefs.getString("model","gpt-4o-mini"),false);form.addView(model);
        gap(form,8);form.addView(text("Clé API (chiffrée sur cet appareil)",13,MUTED,true));apiKey=field("Colle ta clé API ici","",false);apiKey.setInputType(129);form.addView(apiKey);
        form.addView(text("Les modèles ne sont pas tous inclus dans l’APK : ce connecteur utilise le modèle distant choisi chez ton fournisseur.",12,MUTED,false));
        new AlertDialog.Builder(this).setTitle("Configuration IA").setView(form).setNegativeButton("Annuler",(d,w)->{}).setNeutralButton("Tester la connexion",(d,w)->saveSettings(true)).setPositiveButton("Enregistrer",(d,w)->saveSettings(false)).show();
    }
    private void saveSettings(boolean test){
        String url=endpoint.getText().toString().trim(),id=model.getText().toString().trim(),key=apiKey.getText().toString().trim();
        if(!url.startsWith("https://")||id.isEmpty()){toast("URL HTTPS et identifiant de modèle requis.");return;}
        prefs.edit().putString("endpoint",url).putString("model",id).apply();
        if(!key.isEmpty()){try{secure.put("provider_key",key);}catch(Exception e){toast("Chiffrement impossible : "+e.getMessage());return;}}
        status.setText("CONFIGURÉ • "+id);if(test)runProviderTest();else toast("Paramètres enregistrés.");
    }
    private void runProviderTest(){
        status.setText("TEST IA EN COURS…");
        executor.execute(()->{try{String answer=OmniBrain.generate(prefs.getString("endpoint",""),prefs.getString("model",""),secure.get("provider_key"),"Réponds exactement : VANELLE IA OK");runOnUiThread(()->{status.setText("IA CONNECTÉE • réponse reçue");toast("Réponse réelle : "+answer.substring(0,Math.min(100,answer.length())));});}
        catch(Exception e){runOnUiThread(()->{status.setText("IA NON DISPONIBLE • vérifier les paramètres");toast(e.getMessage()==null?"Erreur inconnue":e.getMessage());});}});
    }
    private boolean needsApproval(String s){
        String x=s.toLowerCase(Locale.ROOT);String[] terms={"supprimer","effacer","delete","format","payer","payment","achat","acheter","envoyer un email","send email","publier","publish","installer","désinstaller","shutdown","arrêter le serveur","mot de passe","password","clé privée","private key","virement","transférer de l'argent"};
        for(String term:terms)if(x.contains(term))return true;return false;
    }
    private void submitTask(){
        String request=prompt.getText().toString().trim();if(request.isEmpty()){toast("Décris d’abord la tâche.");return;}
        ((InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(prompt.getWindowToken(),0);
        Task task=new Task(request,needsApproval(request)?"awaiting_approval":"queued");tasks.add(0,task);prompt.setText("");renderTasks();
        if(task.state.equals("awaiting_approval"))new AlertDialog.Builder(this).setTitle("Confirmation requise").setMessage("Cette demande semble sensible. Autorises-tu seulement sa transmission au modèle IA configuré ? Aucun accès externe n’est accordé par cette confirmation.")
            .setNegativeButton("Refuser",(d,w)->{task.state="rejected";task.result="Refusée par l’utilisateur.";renderTasks();}).setPositiveButton("Autoriser l’analyse IA",(d,w)->execute(task)).show();
        else execute(task);
    }
    private void execute(Task task){
        task.state="running";task.result="Analyse en cours…";renderTasks();
        executor.execute(()->{try{
            String answer=OmniBrain.generate(prefs.getString("endpoint","https://api.openai.com/v1"),prefs.getString("model","gpt-4o-mini"),secure.get("provider_key"),
                "Analyse cette demande. Fournis : 1) objectif, 2) plan étape par étape, 3) outils/prérequis, 4) risques et autorisations nécessaires, 5) tests de vérification. Distingue clairement ce qui est proposé de ce qui a réellement été exécuté. Ne prétends pas avoir réalisé une action externe.\n\nDEMANDE : "+task.request);
            runOnUiThread(()->{task.state="completed";task.result=answer;renderTasks();});
        }catch(Exception e){runOnUiThread(()->{task.state="failed";task.result=e.getMessage()==null?"Erreur inconnue":e.getMessage();renderTasks();});}});
    }
    private void renderTasks(){
        if(feed==null)return;feed.removeAllViews();if(tasks.isEmpty()){feed.addView(text("Aucune tâche dans cette session.",13,MUTED,false));return;}
        for(Task task:tasks){LinearLayout card=column();card.setPadding(14,12,14,12);card.setBackground(shape(PANEL,16));card.addView(text(task.state.toUpperCase(Locale.ROOT).replace('_',' '),11,task.state.equals("failed")?RED:CYAN,true));card.addView(text(task.request,14,WHITE,true));
            if(task.result!=null){gap(card,5);card.addView(text(task.result,13,MUTED,false));}
            if(task.state.equals("awaiting_approval"))card.addView(button("Examiner la demande",()->new AlertDialog.Builder(this).setTitle("Autoriser cette demande ?").setMessage(task.request).setNegativeButton("Refuser",(d,w)->{task.state="rejected";task.result="Refusée.";renderTasks();}).setPositiveButton("Autoriser l’analyse IA",(d,w)->execute(task)).show()));
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=10;feed.addView(card,lp);
        }
    }
    private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
    @Override protected void onDestroy(){super.onDestroy();executor.shutdownNow();}
}
