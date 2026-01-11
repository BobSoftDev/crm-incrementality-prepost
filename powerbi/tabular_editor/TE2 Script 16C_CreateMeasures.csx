// TE2 Script: 16C_CreateMeasures.cs
// Constraints: no lambdas, no interpolation, flat statements only.

string mName;
string mExpr;

if (!Model.Tables.Contains("_Measures"))
{
    Model.AddTable("_Measures");
}

// Incrementality (CEO-safe)
mName = "Incremental Revenue";
mExpr = "SUM('Fact Customer Month Incrementality'[incremental_revenue])";
if (!Model.Tables["_Measures"].Measures.Contains(mName))
{
    var m = Model.Tables["_Measures"].AddMeasure(mName, mExpr);
    m.DisplayFolder = "CEO | Incrementality";
    m.FormatString = "#,0.00";
}

mName = "Incremental Transactions";
mExpr = "SUM('Fact Customer Month Incrementality'[incremental_transactions])";
if (!Model.Tables["_Measures"].Measures.Contains(mName))
{
    var m = Model.Tables["_Measures"].AddMeasure(mName, mExpr);
    m.DisplayFolder = "CEO | Incrementality";
    m.FormatString = "#,0";
}

mName = "Average Delta AOV";
mExpr = "AVERAGE('Fact Customer Month Incrementality'[delta_aov])";
if (!Model.Tables["_Measures"].Measures.Contains(mName))
{
    var m = Model.Tables["_Measures"].AddMeasure(mName, mExpr);
    m.DisplayFolder = "CEO | Incrementality";
    m.FormatString = "#,0.00";
}

// Diagnostics (Analyst)
mName = "Pre Revenue per Day";
mExpr = "AVERAGE('Fact Customer Month Incrementality'[pre_rev_per_day])";
if (!Model.Tables["_Measures"].Measures.Contains(mName))
{
    var m = Model.Tables["_Measures"].AddMeasure(mName, mExpr);
    m.DisplayFolder = "Analyst | Baseline";
    m.FormatString = "#,0.00";
}

mName = "Post Revenue per Day";
mExpr = "AVERAGE('Fact Customer Month Incrementality'[post_rev_per_day])";
if (!Model.Tables["_Measures"].Measures.Contains(mName))
{
    var m = Model.Tables["_Measures"].AddMeasure(mName, mExpr);
    m.DisplayFolder = "Analyst | Impact";
    m.FormatString = "#,0.00";
}
