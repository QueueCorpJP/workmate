
import { supabase } from "@/integrations/supabase/client";
import { DashboardStatistics } from "@/types/statistics";

export const fetchDashboardStatistics = async (): Promise<DashboardStatistics> => {
  try {
    const { data, error } = await supabase
      .from('monthly_statistics')
      .select('*')
      .maybeSingle();
    
    if (error) {
      console.error("Error fetching dashboard statistics:", error);
      throw error;
    }
    
    if (!data) {
      console.warn("No statistics data found, returning defaults");
      return {
        total_accounts: 0,
        accounts_change_pct: 0,
        total_inquiries: 0, 
        inquiries_change_pct: 0,
        active_users: 0,
        active_users_change_pct: 0
      };
    }
    
    return data;
  } catch (error) {
    console.error("Unexpected error in fetchDashboardStatistics:", error);
    throw error;
  }
};

export const fetchStatisticsHistory = async (days = 30) => {
  try {
    // Using a direct query on the dashboard_statistics table with no RLS policy dependencies
    const { data, error } = await supabase
      .from('dashboard_statistics')
      .select('id, date, total_accounts, total_inquiries, active_users')
      .order('date', { ascending: false })
      .limit(days);
    
    if (error) {
      console.error("Error fetching statistics history:", error);
      throw error;
    }
    
    return data || [];
  } catch (error) {
    console.error("Unexpected error in fetchStatisticsHistory:", error);
    throw error;
  }
};
