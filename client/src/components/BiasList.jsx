import React from "react";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Divider from "@mui/material/Divider";
import ListItemText from "@mui/material/ListItemText";
import ListItemAvatar from "@mui/material/ListItemAvatar";
import Avatar from "@mui/material/Avatar";
import Typography from "@mui/material/Typography";
import AnchorIcon from "@mui/icons-material/Anchor";
import BlurOnIcon from "@mui/icons-material/BlurOn";
import SearchIcon from "@mui/icons-material/Search";

export default function BiasList({ apophText = "", anchText = "", abductText = "" }) {
  const listSx = {
    width: "100%",
    bgcolor: "transparent",
    color: "#e8edf7",
    p: 0,
  };
  const avatarSx = (color) => ({
    bgcolor: color,
    color: "#0b1220",
    width: 32,
    height: 32,
    fontSize: 18,
  });
  const itemSx = { alignItems: "flex-start", gap: 1, px: 0, py: 1 };
  const textPrimary = { color: "#e8edf7", fontWeight: 600 };
  const textSecondary = { color: "#91a0bf" };

  return (
    <List sx={listSx}>
      <ListItem sx={itemSx} disableGutters>
        <ListItemAvatar sx={{ minWidth: 40 }}>
          <Avatar sx={avatarSx("#5ef0c1")}><BlurOnIcon fontSize="small" /></Avatar>
        </ListItemAvatar>
        <ListItemText
          primary="Apophenia"
          primaryTypographyProps={textPrimary}
          secondary={
            <Typography component="span" variant="body2" sx={textSecondary}>
              {apophText || "—"}
            </Typography>
          }
        />
      </ListItem>
      <Divider component="li" sx={{ borderColor: "rgba(255,255,255,0.08)" }} />
      <ListItem sx={itemSx} disableGutters>
        <ListItemAvatar sx={{ minWidth: 40 }}>
          <Avatar sx={avatarSx("#f7c948")}><AnchorIcon fontSize="small" /></Avatar>
        </ListItemAvatar>
        <ListItemText
          primary="Anchoring"
          primaryTypographyProps={textPrimary}
          secondary={
            <Typography component="span" variant="body2" sx={textSecondary}>
              {anchText || "—"}
            </Typography>
          }
        />
      </ListItem>
      <Divider component="li" sx={{ borderColor: "rgba(255,255,255,0.08)" }} />
      <ListItem sx={itemSx} disableGutters>
        <ListItemAvatar sx={{ minWidth: 40 }}>
          <Avatar sx={avatarSx("#5ef0c1")}><SearchIcon fontSize="small" /></Avatar>
        </ListItemAvatar>
        <ListItemText
          primary="Abductive Reasoning"
          primaryTypographyProps={textPrimary}
          secondary={
            <Typography component="span" variant="body2" sx={textSecondary}>
              {abductText || "—"}
            </Typography>
          }
        />
      </ListItem>
    </List>
  );
}
