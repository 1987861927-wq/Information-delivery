import SwiftUI

struct FavoritesView: View {
    var body: some View {
        NavigationStack {
            ContentUnavailableView("暂无收藏", systemImage: "bookmark", description: Text("收藏的论文和资讯会显示在这里。"))
                .navigationTitle("收藏")
        }
    }
}
