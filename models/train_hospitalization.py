"""
Train hospitalization prediction model.
"""
import pickle
import duckdb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
import xgboost as xgb
from sklearn.metrics import roc_auc_score, classification_report

def train_hospitalization_model():
    """Train XGBoost hospitalization prediction model."""
    print("Loading features...")
    # TODO: Load features from warehouse
    
    print("Splitting data...")
    # Stratified split
    # X_train, X_test, y_train, y_test = train_test_split(...)
    
    print("Training model...")
    model = xgb.XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric='auc',
        early_stopping_rounds=20,
        random_state=42
    )
    # model.fit(X_train_enc, y_train, eval_set=[(X_test_enc, y_test)], verbose=50)
    
    print("Evaluating...")
    # auc = roc_auc_score(y_test, model.predict_proba(X_test_enc)[:,1])
    # print(f"Test AUC: {auc:.4f}")
    
    print("Saving model...")
    # model.save_model('hospitalization_xgb.json')

if __name__ == '__main__':
    train_hospitalization_model()
