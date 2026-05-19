import SwiftUI

struct SearchView: View {
    @State private var query = ""

    var body: some View {
        NavigationStack {
            ContentUnavailableView("搜索", systemImage: "magnifyingglass", description: Text("后续接入后端全文搜索和主题过滤。"))
                .navigationTitle("搜索")
                .searchable(text: $query, prompt: "搜索论文、资讯或关键词")
        }
    }
}
