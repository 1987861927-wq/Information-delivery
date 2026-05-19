import SwiftUI

struct TodayView: View {
    @State private var briefing: Briefing?
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Group {
                if let briefing {
                    List {
                        if !briefing.highlights.isEmpty {
                            Section("今日重点") {
                                ForEach(briefing.highlights) { article in
                                    NavigationLink(value: article) {
                                        ArticleRowView(article: article)
                                    }
                                }
                            }
                        }

                        Section("全部内容") {
                            ForEach(briefing.articles) { article in
                                NavigationLink(value: article) {
                                    ArticleRowView(article: article)
                                }
                            }
                        }
                    }
                    .navigationDestination(for: Article.self) { article in
                        ArticleDetailView(article: article)
                    }
                } else if let errorMessage {
                    ContentUnavailableView("加载失败", systemImage: "exclamationmark.triangle", description: Text(errorMessage))
                } else {
                    ProgressView("加载今日简报...")
                }
            }
            .navigationTitle("今日简报")
            .task {
                await loadBriefing()
            }
        }
    }

    private func loadBriefing() async {
        do {
            briefing = try await APIClient.shared.fetchTodayBriefing()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
