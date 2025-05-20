/**
 * Format a date string to a localized format
 * @param dateString - The date string to format
 * @returns Formatted date string
 */
export const formatDate = (dateString: string): string => {
  if (!dateString) return '情報なし';

  const date = new Date(dateString);
  return new Intl.DateTimeFormat('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date);
};

/**
 * Generate chart data for category distribution
 * @param categories - Object with category names as keys and counts as values
 * @param colors - Array of color strings
 * @returns Chart.js data object
 */
export const getCategoryChartData = (
  categories: Record<string, number> | Array<{category: string, count: number}>,
  colors: string[]
) => {
  // Convert array format to record format if needed
  const categoriesRecord = Array.isArray(categories)
    ? categories.reduce((acc, item) => {
        acc[item.category] = item.count;
        return acc;
      }, {} as Record<string, number>)
    : categories;

  const labels = Object.keys(categoriesRecord);
  const data = Object.values(categoriesRecord);

  return {
    labels,
    datasets: [
      {
        label: 'カテゴリ分布',
        data,
        backgroundColor: colors.slice(0, labels.length),
        borderWidth: 1
      }
    ]
  };
};

/**
 * Generate chart data for sentiment distribution
 * @param sentiments - Object with sentiment names as keys and counts as values
 * @param colors - Object with sentiment names as keys and color strings as values
 * @returns Chart.js data object
 */
export const getSentimentChartData = (
  sentiments: Record<string, number> | Array<{sentiment: string, count: number}>,
  colors: Record<string, string>
) => {
  // Convert array format to record format if needed
  const sentimentsRecord = Array.isArray(sentiments)
    ? sentiments.reduce((acc, item) => {
        acc[item.sentiment] = item.count;
        return acc;
      }, {} as Record<string, number>)
    : sentiments;

  const labels = Object.keys(sentimentsRecord);
  const data = Object.values(sentimentsRecord);

  return {
    labels,
    datasets: [
      {
        label: '感情分布',
        data,
        backgroundColor: labels.map(label => colors[label] || 'rgba(199, 199, 199, 0.6)'),
        borderWidth: 1
      }
    ]
  };
};

/**
 * Convert analysis data to CSV format and trigger download
 * @param analysis - Analysis result data
 */
export const exportAnalysisToCSV = (analysis: any) => {
  try {
    // 今日の日付を取得
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];

    // CSVコンテンツの作成
    let csvContent = "データタイプ,項目,値,割合\n";

    // カテゴリ分布
    let categoryDistribution: Record<string, number>;
    
    if (Array.isArray(analysis.category_distribution)) {
      categoryDistribution = analysis.category_distribution.reduce((acc: Record<string, number>, item: {category: string, count: number}) => {
        acc[item.category] = item.count;
        return acc;
      }, {} as Record<string, number>);
    } else {
      categoryDistribution = analysis.category_distribution;
    }
    
    const categoryValues = Object.values(categoryDistribution) as number[];
    const categoryTotal = categoryValues.reduce((a, b) => a + b, 0);
    
    Object.entries(categoryDistribution).forEach(([category, count]) => {
      const percentage = ((count as number / categoryTotal) * 100).toFixed(2);
      csvContent += `カテゴリ分布,${category},${count},${percentage}%\n`;
    });

    // 感情分布
    let sentimentDistribution: Record<string, number>;
    
    if (Array.isArray(analysis.sentiment_distribution)) {
      sentimentDistribution = analysis.sentiment_distribution.reduce((acc: Record<string, number>, item: {sentiment: string, count: number}) => {
        acc[item.sentiment] = item.count;
        return acc;
      }, {} as Record<string, number>);
    } else {
      sentimentDistribution = analysis.sentiment_distribution;
    }
    
    const sentimentValues = Object.values(sentimentDistribution) as number[];
    const sentimentTotal = sentimentValues.reduce((a, b) => a + b, 0);
    
    Object.entries(sentimentDistribution).forEach(([sentiment, count]) => {
      const percentage = ((count as number / sentimentTotal) * 100).toFixed(2);
      csvContent += `感情分布,${sentiment},${count},${percentage}%\n`;
    });

    // よくある質問
    if (analysis.common_questions && Array.isArray(analysis.common_questions)) {
      analysis.common_questions.forEach((item: any) => {
        if (typeof item === 'string') {
          csvContent += `よくある質問,${item},1\n`;
        } else if (item.question) {
          csvContent += `よくある質問,${item.question},${item.count || 1}\n`;
        }
      });
    }

    // AI洞察
    csvContent += `\nAI洞察\n${analysis.insights.replace(/\n/g, " ")}\n`;

    // 詳細ビジネス分析（存在する場合）
    if (analysis.business_analysis_completed) {
      csvContent += "\n詳細ビジネス分析\n";
      if (analysis.detailed_topic_analysis) {
        csvContent += `\n1. 頻出トピック/質問とその傾向分析\n${analysis.detailed_topic_analysis.replace(/\n/g, " ")}\n`;
      }
      if (analysis.efficiency_opportunities) {
        csvContent += `\n2. 業務効率化の機会\n${analysis.efficiency_opportunities.replace(/\n/g, " ")}\n`;
      }
      if (analysis.frustration_points) {
        csvContent += `\n3. 社員のフラストレーションポイント\n${analysis.frustration_points.replace(/\n/g, " ")}\n`;
      }
      if (analysis.improvement_suggestions) {
        csvContent += `\n4. 製品/サービス改善の示唆\n${analysis.improvement_suggestions.replace(/\n/g, " ")}\n`;
      }
      if (analysis.communication_gaps) {
        csvContent += `\n5. コミュニケーションギャップ\n${analysis.communication_gaps.replace(/\n/g, " ")}\n`;
      }
      if (analysis.specific_recommendations) {
        csvContent += `\n具体的な改善提案\n${analysis.specific_recommendations.replace(/\n/g, " ")}\n`;
      }
    }

    // CSVファイルのダウンロード
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `チャット分析_${dateStr}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error('CSV出力エラー:', error);
    alert('CSV出力中にエラーが発生しました。');
  }
};

/**
 * 
 * @param url 
 * @returns boolean
 */
export const isValidURL = (url: string): boolean =>
  /^(https?:\/\/)?[\w.-]+\.[a-z]{2,}(\S*)$/i.test(url);