// TE2 Script: 16A_BulkRenameTables.cs
// Constraints respected: no lambdas, no local methods, flat statements.

string oldName;
string newName;

oldName = "fact_customer_month_incrementality";
newName = "Fact Customer Month Incrementality";
if (Model.Tables.Contains(oldName)) { Model.Tables[oldName].Name = newName; }

oldName = "agg_incrementality_month";
newName = "Agg Incrementality Month";
if (Model.Tables.Contains(oldName)) { Model.Tables[oldName].Name = newName; }

oldName = "agg_incrementality_rfm";
newName = "Agg Incrementality RFM";
if (Model.Tables.Contains(oldName)) { Model.Tables[oldName].Name = newName; }

oldName = "agg_incrementality_active_value";
newName = "Agg Incrementality Active Value";
if (Model.Tables.Contains(oldName)) { Model.Tables[oldName].Name = newName; }

oldName = "dim_customer_month_rfm";
newName = "Dim Customer Month RFM";
if (Model.Tables.Contains(oldName)) { Model.Tables[oldName].Name = newName; }
